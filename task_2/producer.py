"""
Banking Event Producer

Генерирует события банковских транзакций для PUSH и PULL моделей.
Поддерживает batch-операции и статистику.
"""

import time
import random
from threading import Lock
from typing import Dict, Any, List
from event_manager import BankingEventManager


class BankingEventProducer:
    EVENT_TYPES = ['TRANSACTION', 'DEPOSIT', 'WITHDRAWAL', 'TRANSFER', 'PAYMENT', 'FEE', 'REFUND', 'REVERSAL', 'AUTHORIZATION', 'CAPTURE', 'VOID', 'SETTLEMENT', 'PARTIAL_REFUND', 'PARTIAL_VOID', 'PARTIAL_AUTHORIZATION', 'PARTIAL_CAPTURE', 'PARTIAL_SETTLEMENT']
    CURRENCY_TYPES = ['USD', 'EUR', 'GBP', 'JPY', 'CNY', 'INR', 'BDT', 'PKR', 'NGN', 'ZAR', 'CAD', 'AUD', 'CHF', 'CNY', 'HKD', 'INR', 'MXN', 'NZD', 'RUB', 'SAR', 'SGD', 'THB', 'TRY', 'TWD', 'ZAR']
    STATUS_TYPES = ['PENDING', 'COMPLETED', 'FAILED', 'CANCELLED', 'REFUNDED', 'REVERSED', 'REJECTED', 'EXPIRED', 'AUTHORIZED', 'CAPTURED', 'VOIDED', 'SETTLED', 'PARTIALLY_SETTLED', 'PARTIALLY_REFUNDED', 'PARTIALLY_VOIDED', 'PARTIALLY_AUTHORIZED', 'PARTIALLY_CAPTURED', 'PARTIALLY_REFUNDED', 'PARTIALLY_VOIDED', 'PARTIALLY_AUTHORIZED', 'PARTIALLY_CAPTURED']
    COUNTRY_CODES = ['US', 'GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI', 'PL', 'CZ', 'HU', 'RO', 'BG', 'HR', 'ME', 'AL', 'MK', 'RS', 'SI', 'BA', 'XK']
    CHANNEL_TYPES = ['ATM', 'ONLINE', 'MOBILE', 'BRANCH', 'API', 'POS', 'KIOSK', 'TERMINAL', 'WEB', 'APP', 'SMS', 'EMAIL', 'PHONE', 'CHAT', 'VOICE', 'FAX', 'LETTER', 'MMS', 'PUSH', 'EMAIL', 'PHONE', 'CHAT', 'VOICE', 'FAX', 'LETTER', 'MMS', 'PUSH', 'EMAIL', 'PHONE', 'CHAT', 'VOICE', 'FAX', 'LETTER', 'MMS', 'PUSH', 'EMAIL', 'PHONE', 'CHAT', 'VOICE', 'FAX', 'LETTER', 'MMS', 'PUSH']


    def __init__(self, manager: BankingEventManager, num_events: int = 5000, batch_size: int = 1000, push_mode: bool = False):
        self.manager = manager
        self.num_events = num_events
        self.batch_size = batch_size
        self.push_mode = push_mode

        self.account_ids = [f"ACC{i:06d}" for i in range(1, 10001)]
        self.events_produced = 0
        self.lock = Lock()
        self.start_time = None
        self.end_time = None

    def _generate_event(self, event_id: int) -> Dict[str, Any]:
        return {
            'event_id': event_id,
            'event_type': random.choice(self.EVENT_TYPES),
            'account_id': random.choice(self.account_ids),
            'amount': round(random.uniform(10.0, 1000000.0), 2),
            'timestamp': time.time(),
            'transaction_id': f"TXN{event_id:010d}",
            'metadata': {
                'country_code': random.choice(self.COUNTRY_CODES),
                'channel': random.choice(self.CHANNEL_TYPES),
                'currency': random.choice(self.CURRENCY_TYPES),
                'status': random.choice(self.STATUS_TYPES)
            }
        }

    def produce_events(self) -> None:
        """Генерация событий с batch-поддержкой."""
        self.start_time = time.perf_counter()
        batch: List[Dict[str, Any]] = []

        for i in range(self.num_events):
            ev = self._generate_event(i)
            batch.append(ev)

            if len(batch) >= self.batch_size:
                self._send_batch(batch)
                batch = []

        if batch:
            self._send_batch(batch)

        self.end_time = time.perf_counter()

    def _send_batch(self, batch: List[Dict[str, Any]]) -> None:
        if self.push_mode:
            self.manager.push_events_batch(batch)
        else:
            self.manager.add_events_batch(batch)

        with self.lock:
            self.events_produced += len(batch)

    def get_production_stats(self) -> Dict[str, Any]:
        duration = (self.end_time - self.start_time) if self.start_time and self.end_time else 0
        return {
            'total_produced': self.events_produced,
            'duration': duration,
            'rate': self.events_produced / duration if duration > 0 else 0
        }

