# Configurable Microservice Simulator

## Student Information
1. Student Name: Bekzhanov Namazbek
2. Student ID: 25MD0317
3. Module: Advanced Software Paradigms
4. Assignment: Configurable Microservice Simulator

## How to Run

1. Extract all files to a single folder.
2. Open terminal in that folder.
3. Run the program using: `python main.py`
4. Modify `config.json` to enable/disable services.

### Example Configuration

Default configuration (`config.json`):
```json
{
  "active_services": ["DataCollector", "Analyzer"]
}
```

To add AlertService, modify to:
```json
{
  "active_services": ["DataCollector", "Analyzer", "AlertService"]
}
```

## Short Description

### Services

- **DataCollector**: Simulates sensor readings by generating random temperature values between 18-30°C.
- **Analyzer**: Calculates average temperature from collected readings and detects anomalies.
- **AlertService**: Displays alert messages based on system status monitoring.

### Features

- **Configuration-driven**: Services are activated through `config.json`
- **Modular design**: Each service is an independent module
- **Dynamic loading**: Services are loaded at runtime based on configuration
- **Separation of concerns**: Each service handles a specific responsibility

## Expected Output Example

```
============================================================
  Configurable Microservice Simulator
  Industrial Monitoring System
============================================================

Configuration loaded: 2 service(s) active
Active services: DataCollector, Analyzer

------------------------------------------------------------
Starting services...
------------------------------------------------------------

[DataCollector] Starting data collection...
[DataCollector] Collected readings: [22.3, 23.8, 25.0, 24.7, 23.1]

[Analyzer] Starting data analysis...
[Analyzer] Average temperature: 23.78°C
[Analyzer] ✓ All readings within normal range

------------------------------------------------------------
All configured services completed execution.
============================================================
```

## Project Structure

```
.
├── main.py              # Main controller that loads and runs services
├── config.json          # Configuration file listing active services
├── datacollector.py     # DataCollector service module
├── analyzer.py          # Analyzer service module
├── alertservice.py      # AlertService module
├── README.md            # This file readme.md
└── screenshots          # Program execution screenshots
```
