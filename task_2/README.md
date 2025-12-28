# Banking Event-Based PUSH vs PULL Dispatcher

**Course:** Advanced Software Paradigms, Fall 2025  
**Task 2:** Event-Based PUSH vs PULL Dispatcher  
**Author:** Bekzhanov Namazbek

## Overview

This project implements and compares two event-dispatching models (**PULL** and **PUSH**) in a **realistic banking context**. The system simulates processing millions of banking transactions (deposits, withdrawals, transfers, payments) and stores them efficiently using bulk database operations. Both models are tested under load with **10,000,000 events** to measure their performance characteristics in a production-like banking environment.

## Banking Context

Modern banking systems process millions of transactions daily across multiple channels (ATM, Online, Mobile, Branch, API). This implementation demonstrates how different event dispatching patterns can handle high-volume banking event processing:

- **Transaction Events**: Real-time transaction processing
- **Bulk Operations**: Efficient database persistence using batch inserts
- **Scalability**: Handling 10M+ events with optimal performance
- **Event Types**: TRANSACTION, DEPOSIT, WITHDRAWAL, TRANSFER, PAYMENT, FEE

## Architecture

The implementation consists of four main components:

### 1. `producer.py` - BankingEventProducer
Generates realistic banking events as fast as possible:
- **Event Types**: Multiple banking transaction types
- **Account Simulation**: 10,000 simulated bank accounts
- **Bulk Generation**: Batched event generation for large volumes
- **Two Modes**: PULL (queue-based) and PUSH (direct delivery)

### 2. `event_manager.py` - BankingEventManager
Central component that manages banking event storage and dispatching:
- **Thread-Safe Queue**: For PULL model event storage
- **Callback Registry**: For PUSH model direct delivery
- **Bulk Operations**: Batch event handling for efficiency
- **Event Tracking**: Monitors total events received

### 3. `consumer_pull.py` - BankingConsumerPull
Implements the **PULL model** where:
- Consumer actively requests events from the event manager
- Consumer polls the queue in batches for available events
- **Bulk Database Inserts**: Uses batch operations (simulating PostgreSQL bulk inserts)
- **SQLite Backend**: Stores events in database for persistence
- Consumer processes events at its own pace

### 4. `consumer_push.py` - BankingConsumerPush
Implements the **PUSH model** where:
- Producer pushes events directly to consumers via callbacks
- **Immediate Processing**: Events processed as soon as they're generated
- **Bulk Database Inserts**: Batches events before database writes
- **SQLite Backend**: Stores events in database for persistence
- Lower latency due to direct event delivery

## Key Differences

| Aspect | PULL Model | PUSH Model |
|--------|-----------|------------|
| **Initiative** | Consumer requests events | Producer pushes events |
| **Coupling** | Loose coupling | Tighter coupling |
| **Latency** | Higher (polling overhead) | Lower (immediate delivery) |
| **Resource Usage** | More CPU (polling) | Less CPU (event-driven) |
| **Scalability** | Better for variable rates | Better for consistent rates |
| **Banking Use Case** | Batch processing, reporting | Real-time transaction processing |

## Installation & Usage

### Requirements
- Python 3.9+
- SQLite3 (included with Python)
- No external dependencies (uses only standard library)

### Running the Comparison

```bash
python main.py
```

This will:
1. Run the PULL model with 10,000,000 banking events
2. Run the PUSH model with 10,000,000 banking events
3. Display performance metrics for both models
4. Store events in SQLite databases
5. Print a comprehensive summary comparison

### Expected Output

The script will display:
- Total banking events produced
- Total events processed for each model
- Processing times and throughput rates
- Database storage statistics
- Performance comparison summary

### Testing with Smaller Event Counts

For faster testing, modify `num_events` in `main.py`:

```python
num_events = 5000  # For quick testing
# or
num_events = 100000  # For medium testing
# or
num_events = 10000000  # For full banking scenario
```

## Performance Results

Based on test runs with 10,000,000 banking events:

- **Total Events Produced:** 10,000,000
- **PULL Model:** Processes events using queue-based polling with bulk database inserts
- **PUSH Model:** Processes events using direct delivery with bulk database inserts

**Key Performance Factors:**
- Bulk database operations significantly improve throughput
- PUSH model eliminates polling overhead
- Batch processing (5000 events per batch) optimizes database writes
- Both models achieve high throughput with proper batching

## Project Structure

```
.
├── producer.py          # Banking event producer implementation
├── event_manager.py     # Banking event management and dispatching
├── consumer_pull.py     # PULL model consumer with database
├── consumer_push.py     # PUSH model consumer with database
├── main.py              # Main comparison script
├── summary.txt          # Performance summary and banking analysis
├── README.md            # This file
├── banking_events_pull.db  # SQLite database (PULL model) - generated
└── banking_events_push.db  # SQLite database (PUSH model) - generated
```

## Design Decisions

1. **Banking Event Structure**: Events include realistic banking fields:
   - Event type (TRANSACTION, DEPOSIT, WITHDRAWAL, etc.)
   - Account ID (10,000 simulated accounts)
   - Amount, timestamp, transaction ID
   - Channel (ATM, ONLINE, MOBILE, BRANCH, API)
   - Metadata (currency, status)

2. **Bulk Database Operations**: 
   - Uses `executemany()` for batch inserts (simulating PostgreSQL bulk inserts)
   - Batch size of 5000 events optimizes performance
   - Reduces database round-trips significantly

3. **Thread Safety**: 
   - All components use thread-safe data structures
   - `queue.Queue` for PULL model
   - `threading.Lock` for shared state

4. **High-Precision Timing**: 
   - Uses `time.perf_counter()` for accurate performance measurements
   - Handles division by zero errors gracefully

5. **Database Schema**: 
   - Indexed tables for fast queries
   - Stores both structured data and JSON payload
   - Supports banking event analytics

## Banking Use Cases

### PULL Model - Best For:
- **Batch Processing**: End-of-day transaction reconciliation
- **Reporting Systems**: Generating daily/monthly reports
- **Data Warehousing**: ETL processes for analytics
- **Variable Load**: Systems with fluctuating processing capacity

### PUSH Model - Best For:
- **Real-Time Processing**: Immediate transaction validation
- **Fraud Detection**: Instant event analysis
- **Notification Systems**: Immediate customer alerts
- **Consistent Load**: Systems with stable processing capacity

## Code Quality

- Clean, readable code with descriptive variable names
- Comprehensive docstrings for all classes and methods
- Type hints for better code clarity
- Short, focused English comments
- Follows Python PEP 8 style guidelines
- Error handling for edge cases (division by zero, empty batches)

## Database Operations

The implementation uses SQLite for simplicity but is designed to work with PostgreSQL in production:

```python
# PostgreSQL bulk insert equivalent:
cursor.executemany("""
    INSERT INTO banking_events 
    (event_id, event_type, account_id, amount, ...)
    VALUES (%s, %s, %s, %s, ...)
""", values)
```

For production PostgreSQL deployment:
- Use `psycopg2` or `asyncpg` for connection pooling
- Implement connection pooling for high concurrency
- Use `COPY` command for maximum bulk insert performance
- Configure batch sizes based on network latency

## Future Enhancements

Potential improvements for production banking systems:
- **PostgreSQL Integration**: Replace SQLite with PostgreSQL
- **Kafka Integration**: Use Kafka for event streaming
- **Multiple Consumers**: Support for multiple concurrent consumers
- **Event Filtering**: Route events based on type or account
- **Priority Queues**: Process high-priority transactions first
- **Asynchronous Processing**: Use `asyncio` for better concurrency
- **Metrics Dashboard**: Real-time performance monitoring
- **Error Handling**: Retry logic and dead letter queues
- **Event Replay**: Ability to reprocess events from database

## License

This project is created for educational purposes as part of the Advanced Software Paradigms course.
