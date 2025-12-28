"""
Banking Consumer PUSH

Обрабатывает события, отправляемые напрямую продюсером (PUSH).
Использует batch insert для базы данных.
"""

import time
import threading
import sqlite3
import json
import os
from typing import List, Dict, Any
from event_manager import BankingEventManager


class BankingConsumerPush:
    def __init__(self, manager: BankingEventManager, batch_size: int = 1000, db_path: str = "banking_events_push.db"):
        self.manager = manager
        self.batch_size = batch_size
        self.db_path = db_path

        self.event_batch: List[Dict[str, Any]] = []
        self.batch_lock = threading.Lock()
        self.events_processed = 0
        self.lock = threading.Lock()
        self.start_time = None
        self.end_time = None

        self._init_database()

    def _init_database(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS banking_events (
                event_id INTEGER PRIMARY KEY,
                event_type TEXT NOT NULL,
                account_id TEXT NOT NULL,
                amount REAL NOT NULL,
                timestamp REAL NOT NULL,
                transaction_id TEXT UNIQUE NOT NULL,
                country_code CHAR(2),
                channel TEXT,
                currency TEXT,
                status TEXT,
                processed_at REAL,
                payload JSON
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_account_id ON banking_events(account_id, country_code, channel)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON banking_events(timestamp, country_code, channel)")
        conn.commit()
        conn.close()
    def on_event_received(self, event: Dict[str, Any]):
        if self.start_time is None:
            self.start_time = time.perf_counter()

        with self.batch_lock:
            self.event_batch.append(event)
            if len(self.event_batch) >= self.batch_size:
                self._process_batch()

    def _process_batch(self):
        batch_to_insert = self.event_batch.copy()
        self.event_batch = []
        self._bulk_insert(batch_to_insert)
        with self.lock:
            self.events_processed += len(batch_to_insert)

    def _bulk_insert(self, events: List[Dict[str, Any]]):
        if not events:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        data = [
            (
                e['event_id'], e['event_type'], e['account_id'], e['amount'], e['timestamp'],
                e['transaction_id'], e['metadata'].get('country_code'), e['metadata'].get('channel'), e['metadata'].get('currency'),
                e['metadata'].get('status'), time.time(), json.dumps(e)
            )
            for e in events
        ]

        cursor.executemany("""
            INSERT OR IGNORE INTO banking_events 
            (event_id, event_type, account_id, amount, timestamp, transaction_id, country_code, channel, currency, status, processed_at, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        conn.commit()
        conn.close()

    def register(self):
        self.manager.register_push_callback(self.on_event_received)

    def finish(self):
        with self.batch_lock:
            if self.event_batch:
                self._process_batch()
        self.end_time = time.perf_counter()

    def get_processing_stats(self):
        duration = (self.end_time - self.start_time) if self.start_time and self.end_time else 0
        return {
            'total_processed': self.events_processed,
            'duration': duration,
            'rate': self.events_processed / duration if duration > 0 else 0
        }

    def get_database_stats(self):
        if not os.path.exists(self.db_path):
            return {'stored_count': 0}
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM banking_events")
        count = cursor.fetchone()[0]
        conn.close()
        return {'stored_count': count}
