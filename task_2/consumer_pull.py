"""
Banking Consumer PULL

Обрабатывает события, которые помещаются в очередь (PULL).
Использует batch insert для базы данных.
"""

import time
import threading
import sqlite3
import json
import os
from typing import List, Dict, Any
from event_manager import BankingEventManager


class BankingConsumerPull:
    def __init__(self, manager: BankingEventManager, batch_size: int = 1000, db_path: str = "banking_events_pull.db"):
        self.manager = manager
        self.batch_size = batch_size
        self.db_path = db_path

        self.events_processed = 0
        self.lock = threading.Lock()
        self.start_time = None
        self.end_time = None
        self.running = False

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

    def start_consuming(self):
        self.running = True
        batch: List[Dict[str, Any]] = []
        self.start_time = time.perf_counter()

        while self.running or self.manager.has_events():
            event = self.manager.get_event(timeout=0.05)
            if event:
                batch.append(event)
                if len(batch) >= self.batch_size:
                    self._bulk_insert(batch)
                    with self.lock:
                        self.events_processed += len(batch)
                    batch = []

        if batch:
            self._bulk_insert(batch)
            with self.lock:
                self.events_processed += len(batch)
        self.end_time = time.perf_counter()

    def stop(self):
        self.running = False

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
