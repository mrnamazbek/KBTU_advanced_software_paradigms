"""
Main script to run and compare PULL vs PUSH event dispatching models.
Banking-focused implementation with database persistence and bulk operations.
"""

import threading
import time
import random
from producer import BankingEventProducer
from event_manager import BankingEventManager
from consumer_pull import BankingConsumerPull
from consumer_push import BankingConsumerPush


def run_pull_model(num_events: int, batch_size: int):
    print("\n" + "="*70)
    print("Running PULL Model (Banking Events)")
    print("="*70)

    # Initialize components
    manager = BankingEventManager()
    producer = BankingEventProducer(manager, num_events=num_events, batch_size=batch_size, push_mode=False)
    consumer = BankingConsumerPull(manager, batch_size=batch_size)

    # Start consumer thread
    consumer_thread = threading.Thread(target=consumer.start_consuming, daemon=True)
    consumer_thread.start()

    # Small delay to ensure consumer is ready
    time.sleep(0.01)

    # Produce events
    print(f"Producing {num_events:,} events...")
    producer.produce_events()

    # Wait for consumer to process all events
    consumer.stop()
    consumer_thread.join(timeout=max(60, num_events // 1000))
    time.sleep(0.05)  # allow final batch

    # Collect statistics
    prod_stats = producer.get_production_stats()
    cons_stats = consumer.get_processing_stats()
    db_stats = consumer.get_database_stats()

    print(f"\nProduction Stats: {prod_stats}")
    print(f"Processing Stats: {cons_stats}")
    print(f"DB Stats: {db_stats}")

    return {
        'produced': prod_stats['total_produced'],
        'processed': cons_stats['total_processed'],
        'prod_time': prod_stats['duration'],
        'proc_time': cons_stats['duration'],
        'db_stored': db_stats['stored_count']
    }


def run_push_model(num_events: int, batch_size: int):
    print("\n" + "="*70)
    print("Running PUSH Model (Banking Events)")
    print("="*70)

    # Initialize components
    manager = BankingEventManager()
    consumer = BankingConsumerPush(manager, batch_size=batch_size)
    consumer.register()
    producer = BankingEventProducer(manager, num_events=num_events, batch_size=batch_size, push_mode=True)

    # Produce events (pushed directly)
    print(f"Producing {num_events:,} events...")
    producer.produce_events()

    # Finish consumer
    time.sleep(0.01)
    consumer.finish()

    # Collect statistics
    prod_stats = producer.get_production_stats()
    cons_stats = consumer.get_processing_stats()
    db_stats = consumer.get_database_stats()

    print(f"\nProduction Stats: {prod_stats}")
    print(f"Processing Stats: {cons_stats}")
    print(f"DB Stats: {db_stats}")

    return {
        'produced': prod_stats['total_produced'],
        'processed': cons_stats['total_processed'],
        'prod_time': prod_stats['duration'],
        'proc_time': cons_stats['duration'],
        'db_stored': db_stats['stored_count']
    }


def main():
    # Random number of events between 500 thousand and 1 million
    num_events = random.randint(500_000, 1_000_000)
    batch_size = max(500, min(5000, num_events // 1000))

    print(f"\nNumber of events: {num_events:,}, Batch size: {batch_size:,}\n")
    print("="*70)
    print("BANKING EVENT-BASED PUSH vs PULL DISPATCHER COMPARISON")
    print("="*70)

    # Run PULL model
    print("\n[1/2] Running PULL Model...")
    pull_results = run_pull_model(num_events, batch_size)
    time.sleep(2)

    # Run PUSH model
    print("\n[2/2] Running PUSH Model...")
    push_results = run_push_model(num_events, batch_size)

    # Summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print(f"Total Events Produced: {pull_results['produced']:,}")
    print(f"PULL Processed: {pull_results['processed']:,} | PUSH Processed: {push_results['processed']:,}")
    print(f"PULL DB Stored: {pull_results['db_stored']:,} | PUSH DB Stored: {push_results['db_stored']:,}")

    print("\nPerformance Metrics:")
    print(f"PULL Processing Time: {pull_results['proc_time']:.2f}s | Rate: {pull_results['processed']/pull_results['proc_time'] if pull_results['proc_time']>0 else 0:,.2f} events/sec")
    print(f"PUSH Processing Time: {push_results['proc_time']:.2f}s | Rate: {push_results['processed']/push_results['proc_time'] if push_results['proc_time']>0 else 0:,.2f} events/sec")
    print("="*70 + "\n")

    return {
        'pull': pull_results,
        'push': push_results
    }


if __name__ == "__main__":
    results = main()
