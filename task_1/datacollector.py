"""
DataCollector Service Module
simulates sensor readings from industrial sensors.
"""
import random


class DataCollector:
    """service that collects fake sensor readings from industrial sensors."""
    
    def __init__(self):
        self.service_name = "DataCollector"
        self.readings = []
    
    def collect_sensor_data(self):
        """generate random sensor readings simulating temperature sensors."""
        # generating 5 random temperature readings between 18 and 30 degrees Celsius
        self.readings = [round(random.uniform(18.0, 30.0), 1) for _ in range(5)]
        return self.readings
    
    def run(self):
        """main entry point for DataCollector service."""
        print(f"[{self.service_name}] Starting data collection...")
        readings = self.collect_sensor_data()
        print(f"[{self.service_name}] Collected readings: {readings}")
        return readings
