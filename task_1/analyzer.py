"""
Analyzer Service Module
"""
import random


class Analyzer:
    """service that analyzes sensor data and computes statistics."""
    
    def __init__(self, data_collector=None):
        self.service_name = "Analyzer"
        self.data_collector = data_collector
        self.readings = []
    
    def analyze_data(self, readings):
        """
        return average temperature value.
        """
        if not readings:
            return None
        
        average_temp = sum(readings) / len(readings)
        return round(average_temp, 2)
    
    def detect_anomalies(self, readings):
        """
        return true if anomaly detected, false otherwise.
        """
        normal_min, normal_max = 15.0, 35.0
        for reading in readings:
            if reading < normal_min or reading > normal_max:
                return True
        return False
    
    def run(self):
        """main entry point for Analyzer service."""
        print(f"[{self.service_name}] Starting data analysis...")
        
        # if no data collector provided, generate random sample data
        if not self.readings:
            if self.data_collector:
                self.readings = self.data_collector.readings if hasattr(self.data_collector, 'readings') else []
            else:
                # generate random temperatures
                self.readings = [round(random.uniform(18.0, 30.0), 1) for _ in range(5)]
        
        if self.readings:
            avg_temp = self.analyze_data(self.readings)
            print(f"[{self.service_name}] Average temperature: {avg_temp}°C")
            
            if self.detect_anomalies(self.readings):
                print(f"[{self.service_name}] anomaly detected in readings!")
            else:
                print(f"[{self.service_name}] all readings within normal range")
        
        return self.readings
