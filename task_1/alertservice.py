"""
AlertService Module
"""
import random


class AlertService:
    """monitoring system status and displaying alerts."""
    
    def __init__(self, threshold=25.0):
        self.service_name = "AlertService"
        self.threshold = threshold  # threshold for alerts
        self.status = "normal"
    
    def check_status(self, readings=None):
        """
        return status based on sensor readings.
        """
        if readings:
            avg_temp = sum(readings) / len(readings) if readings else 0
            if avg_temp > self.threshold:
                self.status = "warning"
            else:
                self.status = "normal"
        else:
            # random status
            statuses = ["normal", "warning", "critical"]
            self.status = random.choice(statuses)
        
        return self.status
    
    def get_alert_message(self):
        """return alert message based on system status."""
        if self.status == "warning":
            return "ALERT! Value exceeds threshold!"
        elif self.status == "critical":
            return "CRITICAL ALERT! Immediate action required!"
        else:
            return "System running normally."
    
    def run(self):
        """main entry point for AlertService."""
        print(f"[{self.service_name}] Checking system status...")
        
        # simulate status check
        self.check_status()
        message = self.get_alert_message()
        
        print(f"[{self.service_name}] {message}")
        
        return self.status
