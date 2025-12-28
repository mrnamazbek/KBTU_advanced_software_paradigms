"""
event_manager.py

Banking Event Manager - improved implementation.

Features:
- Thread-safe in-memory queue for PULL model (uses queue.Queue with task_done/join).
- True batch PUSH model (push_batches) and single-event push.
- Register either per-event callbacks or batch callbacks.
- Callbacks are invoked without holding internal locks to avoid blocking producers.
- Optional asynchronous dispatch (ThreadPoolExecutor) to offload callback execution.
- Graceful shutdown support and simple stats.
"""

from typing import Optional, Dict, Any, Callable, List
import threading
import queue
import time
import logging
from concurrent.futures import ThreadPoolExecutor, Executor

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# Types for callbacks
Event = Dict[str, Any]
EventCallback = Callable[[Event], None]
EventBatchCallback = Callable[[List[Event]], None]


class BankingEventManager:
    """
    Manages banking event storage and dispatching for both PULL and PUSH models.

    Usage patterns:
      - Producer: event_manager.add_event(event) or add_events_batch([...])
      - PULL Consumer: event = event_manager.get_event(); ...; event_manager.task_done()
      - Or use get_events_batch(batch_size) which returns up to batch_size events.
      - PUSH Consumer: register_push_callback(cb) for single events, or
                       register_push_batch_callback(cb_batch) for batches.
      - To stop and wait: event_manager.stop(); event_manager.join()
    """

    def __init__(
        self,
        max_queue_size: int = 0,
        push_executor_workers: Optional[int] = None,
    ):
        """
        Args:
            max_queue_size: maximum size of the internal queue (0 = unlimited).
            push_executor_workers: if provided (>0), use a ThreadPoolExecutor with that many workers
                                   to asynchronously call push callbacks (prevents producer blocking).
        """
        self.events: queue.Queue = queue.Queue(maxsize=max_queue_size) if max_queue_size > 0 else queue.Queue()
        self._queue_lock = threading.Lock()

        # Push callbacks: per-event and per-batch
        self._push_event_callbacks: List[EventCallback] = []
        self._push_batch_callbacks: List[EventBatchCallback] = []
        self._push_lock = threading.Lock()

        # Optional executor to call callbacks asynchronously (so producer doesn't block)
        self._push_executor: Optional[Executor] = None
        if push_executor_workers and push_executor_workers > 0:
            self._push_executor = ThreadPoolExecutor(max_workers=push_executor_workers)

        # Counters and control
        self._total_events_received = 0
        self._total_events_pushed = 0
        self._total_events_queued = 0

        self._stopped = threading.Event()

    # ---------------------------
    # PULL: adding events
    # ---------------------------
    def add_event(self, event: Event, block: bool = False, timeout: Optional[float] = None) -> None:
        """
        Add a single event to the queue for PULL consumers.

        Args:
            event: event dict
            block: whether to block if the queue is full
            timeout: timeout for blocking put
        """
        try:
            if block:
                self.events.put(event, block=True, timeout=timeout)
            else:
                self.events.put_nowait(event)
            with self._queue_lock:
                self._total_events_received += 1
                self._total_events_queued += 1
        except queue.Full:
            # fallback: block briefly to avoid losing the event
            logger.warning("Queue full - blocking put for event")
            self.events.put(event, block=True, timeout=1.0)
            with self._queue_lock:
                self._total_events_received += 1
                self._total_events_queued += 1

    def add_events_batch(self, events: List[Event], block: bool = False) -> None:
        """
        Add a list of events to the queue. Attempts to use non-blocking puts first.

        Args:
            events: list of event dicts
            block: whether to block when queue is full for put
        """
        for ev in events:
            # try nowait for speed; fallback to blocking put if needed
            try:
                self.add_event(ev, block=block)
            except Exception:
                # fallback - ensure event is added
                logger.exception("Error adding event in batch, retrying with blocking put")
                self.add_event(ev, block=True, timeout=1.0)

    # ---------------------------
    # PULL: getting events
    # ---------------------------
    def get_event(self, timeout: Optional[float] = None) -> Optional[Event]:
        """
        Get a single event from the queue.

        Args:
            timeout: seconds to wait for an event; None means block until available.

        Returns:
            Event dict or None if timeout occurred.
        """
        try:
            ev = self.events.get(timeout=timeout)
            return ev
        except queue.Empty:
            return None

    def get_events_batch(self, batch_size: int, timeout: Optional[float] = None) -> List[Event]:
        """
        Get up to batch_size events from queue. This blocks for the first event up to `timeout`,
        then drains available events with non-blocking calls.

        Args:
            batch_size: maximum number of events to return
            timeout: how long to wait for the first event (None => block indefinitely)

        Returns:
            list of events (may be empty)
        """
        batch: List[Event] = []
        first = self.get_event(timeout=timeout)
        if first is None:
            return batch
        batch.append(first)
        # drain rest quickly without blocking
        for _ in range(batch_size - 1):
            try:
                ev = self.events.get_nowait()
                batch.append(ev)
            except queue.Empty:
                break
        return batch

    def task_done(self, n: int = 1) -> None:
        """
        Indicate that the consumer has finished processing n items retrieved from the queue.
        This delegates to queue.task_done() n times.
        """
        for _ in range(n):
            try:
                self.events.task_done()
                with self._queue_lock:
                    # Decrement queued counter (best-effort)
                    if self._total_events_queued > 0:
                        self._total_events_queued -= 1
            except Exception:
                # ignore task_done if not matching get/join
                logger.debug("task_done called too many times or when queue not tracked")

    def join(self, timeout: Optional[float] = None) -> None:
        """
        Block until all items in the queue have been processed (queue.join()).
        """
        try:
            self.events.join()  # may block until task_done called for each item
        except Exception:
            logger.exception("Error while waiting for queue.join()")

    # ---------------------------
    # PUSH: callback registration
    # ---------------------------
    def register_push_callback(self, callback: EventCallback) -> None:
        """
        Register a single-event callback for PUSH model.
        Callback signature: callback(event_dict)
        """
        with self._push_lock:
            self._push_event_callbacks.append(callback)

    def unregister_push_callback(self, callback: EventCallback) -> None:
        """Unregister previously registered per-event callback (if present)."""
        with self._push_lock:
            try:
                self._push_event_callbacks.remove(callback)
            except ValueError:
                pass

    def register_push_batch_callback(self, callback: EventBatchCallback) -> None:
        """
        Register a batch callback for PUSH model.
        Callback signature: callback(list_of_event_dicts)
        """
        with self._push_lock:
            self._push_batch_callbacks.append(callback)

    def unregister_push_batch_callback(self, callback: EventBatchCallback) -> None:
        """Unregister previously registered batch callback (if present)."""
        with self._push_lock:
            try:
                self._push_batch_callbacks.remove(callback)
            except ValueError:
                pass

    # ---------------------------
    # PUSH: pushing events
    # ---------------------------
    def push_event(self, event: Event) -> None:
        """
        Push a single event to registered callbacks.

        This method:
          - grabs a snapshot of callbacks under lock,
          - then calls callbacks WITHOUT holding the lock (to avoid blocking registration or other pushes).
          - if a push_executor is configured, callbacks will be submitted to the executor to avoid blocking producer.
        """
        with self._push_lock:
            event_callbacks = list(self._push_event_callbacks)
            batch_callbacks = list(self._push_batch_callbacks)

        # If a batch callback is present, prefer to call it with single-item batch
        if batch_callbacks:
            self._dispatch_batch_to_callbacks(batch_callbacks, [event])
        # Then call per-event callbacks
        if event_callbacks:
            self._dispatch_to_callbacks(event_callbacks, event)

        # update counters
        with self._queue_lock:
            self._total_events_received += 1
            self._total_events_pushed += 1

    def push_events_batch(self, events: List[Event]) -> None:
        """
        Push a list of events to registered batch callbacks. If there are no batch callbacks,
        fallback to pushing events individually to per-event callbacks.

        Important: this method does NOT block on callback execution if an executor is provided.
        """
        if not events:
            return

        with self._push_lock:
            batch_callbacks = list(self._push_batch_callbacks)
            event_callbacks = list(self._push_event_callbacks)

        if batch_callbacks:
            # deliver as real batch to batch callbacks
            self._dispatch_batch_to_callbacks(batch_callbacks, events)

        if event_callbacks:
            # if per-event callbacks exist, deliver each event (but do not hold locks)
            for ev in events:
                self._dispatch_to_callbacks(event_callbacks, ev)

        with self._queue_lock:
            self._total_events_received += len(events)
            # We don't increment queued counter because these events were pushed, not queued
            self._total_events_pushed += len(events)

    # Helper dispatchers
    def _dispatch_to_callbacks(self, callbacks: List[EventCallback], event: Event) -> None:
        """Call per-event callbacks (possibly via executor)."""
        if self._push_executor:
            for cb in callbacks:
                try:
                    self._push_executor.submit(self._safe_call, cb, event)
                except Exception:
                    logger.exception("Failed to submit callback to executor")
        else:
            for cb in callbacks:
                self._safe_call(cb, event)

    def _dispatch_batch_to_callbacks(self, callbacks: List[EventBatchCallback], events: List[Event]) -> None:
        """Call batch callbacks (possibly via executor)."""
        if self._push_executor:
            for cb in callbacks:
                try:
                    # submit the full batch to executor
                    self._push_executor.submit(self._safe_call, cb, events)
                except Exception:
                    logger.exception("Failed to submit batch callback to executor")
        else:
            for cb in callbacks:
                self._safe_call(cb, events)

    @staticmethod
    def _safe_call(cb: Callable, payload) -> None:
        """Call a callback and catch exceptions to avoid breaking the manager."""
        try:
            cb(payload)
        except Exception as exc:
            logger.exception("Exception in push callback: %s", exc)

    # ---------------------------
    # Control & stats
    # ---------------------------
    def stop(self) -> None:
        """
        Signal the manager to stop. This does not forcibly clear the queue;
        consumers should finish processing events and call task_done().
        """
        self._stopped.set()

    def stopped(self) -> bool:
        """Return True if stop() was called."""
        return self._stopped.is_set()

    def get_queue_size(self) -> int:
        """Return number of items currently queued for PULL consumers."""
        return self.events.qsize()

    def has_events(self) -> bool:
        """True when queue is not empty."""
        return not self.events.empty()

    def get_total_received(self) -> int:
        """Return total events received (both queued and pushed)."""
        with self._queue_lock:
            return int(self._total_events_received)

    def get_total_pushed(self) -> int:
        with self._queue_lock:
            return int(self._total_events_pushed)

    def get_total_queued(self) -> int:
        with self._queue_lock:
            return int(self._total_events_queued)
