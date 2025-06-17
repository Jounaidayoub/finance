import json
from datetime import datetime
from ..processing.Connection import Connection
from src.alerting.email_service import send_alert_email

class AnomalyAlertManager:
    def __init__(self, anomaly_threshold=10, email_recipient=None):
        self.anomaly_threshold = anomaly_threshold
        self.email_recipient = email_recipient
        self.redis = Connection.get_redis()
        self.redis_key = "anomaly_email_queue"

    def process_anomaly(self, anomaly_record):
        """
        Processes a new anomaly record, stores it in Redis, and triggers an email
        if the anomaly count reaches the threshold.
        """
        # Store the anomaly record as a JSON string in Redis
        self.redis.lpush(self.redis_key, json.dumps(anomaly_record))
        # Keep only the last 'anomaly_threshold' anomalies
        self.redis.ltrim(self.redis_key, 0, self.anomaly_threshold - 1)

        current_anomaly_count = self.redis.llen(self.redis_key)
        print(f"Current anomaly count in queue: {current_anomaly_count}")

        if current_anomaly_count == self.anomaly_threshold:
            print(f"Anomaly count reached {self.anomaly_threshold}. Sending aggregated email.")
            self._send_aggregated_email()
            # Clear the queue after sending the email
            self.redis.delete(self.redis_key)
            print("Anomaly queue cleared.")

    def _send_aggregated_email(self):
        """
        Retrieves the last 'anomaly_threshold' anomalies from Redis,
        formats them, and sends an aggregated email.
        """
        anomalies_raw = self.redis.lrange(self.redis_key, 0, self.anomaly_threshold - 1)
        anomalies = [json.loads(record) for record in anomalies_raw]

        subject = f"Aggregated Anomaly Alert: {self.anomaly_threshold} Recent Anomalies"
        body_parts = [f"Detected {self.anomaly_threshold} anomalies:\n"]

        for i, anomaly in enumerate(anomalies):
            symbol = anomaly.get('symbol', 'N/A')
            price = anomaly.get('price', 'N/A')
            timestamp = anomaly.get('timestamp', 'N/A')
            alert_type = anomaly.get('alert_type', 'N/A')
            change_pct = anomaly.get('change_pct', 0.0)
            z_score = anomaly.get('details', {}).get('z_score', 'N/A')
            sma = anomaly.get('details', {}).get('sma', 'N/A')
            deviation_pct = anomaly.get('details', {}).get('deviation_pct', 'N/A')

            body_parts.append(f"--- Anomaly {i+1} ---")
            body_parts.append(f"Symbol: {symbol}")
            body_parts.append(f"Price: {price}")
            body_parts.append(f"Timestamp: {timestamp}")
            body_parts.append(f"Alert Type: {alert_type}")
            if alert_type in ["rise", "drop"]:
                body_parts.append(f"Change/Deviation: {change_pct:+.2f}%")
            if z_score != 'N/A':
                body_parts.append(f"Z-Score: {z_score:.2f}")
            if sma != 'N/A':
                body_parts.append(f"SMA: {sma:.2f}")
                body_parts.append(f"Deviation from SMA: {deviation_pct:.2f}%")
            body_parts.append("\n")

        full_body = "\n".join(body_parts)
        send_alert_email(subject, full_body, self.email_recipient)

# You can instantiate the manager globally or pass it around
# For example, if you want a singleton:
