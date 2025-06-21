from datetime import datetime
import json
from src.processing.Connection import Connection
from src.processing.detection_interface import DetectionAlgorithm

from ..alerting.anomaly_alert_manager import AnomalyAlertManager

# Instantiate the AnomalyAlertManager
anomaly_manager = AnomalyAlertManager(anomaly_threshold=10)


from src.processing.utils import put_to_index

class ZScoreDetectionAlgorithm(DetectionAlgorithm):
    def detect(self, price):
        producer = Connection.getproducer()
        redis = Connection.get_redis()
        es = Connection.get_elasticsearch()
        symbol = price.get('symbol', 'N/A')
        redis_key = f"last_10_prices_{symbol}"
        redis.lpush(redis_key, price['close'])
        redis.ltrim(redis_key, 0, 9)

        last_10 = redis.lrange(redis_key, 0, -1)

        if len(last_10) > 1:
            prev_price = float(last_10[1])
            curr_price = float(price.get('close', 0.0))
            change_pct = (curr_price - prev_price) / prev_price * 100
            alert_type = "rise" if change_pct > 0 else "drop"
        else:
            change_pct = 0.0
            alert_type = None

        window = last_10
        mean = sum(float(x) for x in window) / len(window)
        std = (sum(((float(x) - mean) ** 2 for x in window)) / len(window)) ** (1 / 2)

        z_score = (float(price['close']) - mean) / std if std != 0 else 0.0

        if abs(z_score) > 2.5 and alert_type:
            message = f"{price['symbol']}{'🟩' if alert_type == 'rise' else '🟥'}ALERT[{change_pct:+.2f}%]: Price {price['close']} has a high z_score {z_score}"
            formatted_date = datetime.strptime(price['timestamp'], "%Y-%m-%d %H:%M:%S")
            anomaly_document = {
                "symbol": price['symbol'],
                "price": price['close'],
                "timestamp": formatted_date.isoformat(),
                "alert_type": alert_type,
                "change_pct": change_pct,
                "timestamp_detection": datetime.now().isoformat(),
                "data_point": price['close'],
                "full_record": json.dumps(price),
                "details": {
                    "z_score": z_score,
                    "mean": mean,
                    "std_dev": std
                }
            }
            es.index(index="anomalies_test", document=anomaly_document)
            # anomaly_manager.process_anomaly(anomaly_document) # Process anomaly for email alerts
            producer.send("alerts", value=message)
            producer.flush()
            put_to_index(price, client=es)
            return f"{'🟩' if alert_type == 'rise' else '🟥'} ALERT : Price {price} has been sent to the alerts topic"
        else:
            put_to_index(price, client=es)
            return f"💹 Price {price['close']} is within the normal range , the Z_score : {z_score}"

class SMADetectionAlgorithm(DetectionAlgorithm):
    def detect(self, price):
        producer = Connection.getproducer()
        es = Connection.get_elasticsearch()
        redis = Connection.get_redis()

        symbol = price.get('symbol', 'N/A')
        current_price = float(price.get('close', 0.0))
        
        # Use a longer window for SMA, e.g., 20 prices
        SMA_WINDOW_SIZE = 20
        redis_key = f"last_{SMA_WINDOW_SIZE}_prices_{symbol}"
        redis.lpush(redis_key, current_price)
        redis.ltrim(redis_key, 0, SMA_WINDOW_SIZE - 1)
        
        prices_for_sma = [float(x) for x in redis.lrange(redis_key, 0, -1)]

        if len(prices_for_sma) == SMA_WINDOW_SIZE:
            sma = sum(prices_for_sma) / SMA_WINDOW_SIZE
            
            # Define a deviation threshold, e.g., 5% deviation from SMA
            DEVIATION_THRESHOLD_PERCENT = 5.0

            deviation_pct = abs((current_price - sma) / sma) * 100

            if deviation_pct > DEVIATION_THRESHOLD_PERCENT:
                alert_type = "rise" if current_price > sma else "drop"
                message = f"{price['symbol']}{'🟩' if alert_type == 'rise' else '🟥'}ALERT[{deviation_pct:.2f}% deviation]: Price {current_price} deviates significantly from SMA {sma:.2f}"
                
                formatted_date = datetime.strptime(price['timestamp'], "%Y-%m-%d %H:%M:%S")
                anomaly_document = {
                    "symbol": price['symbol'],
                    "price": price['close'],
                    "timestamp": formatted_date.isoformat(),
                    "alert_type": alert_type,
                    "change_pct": deviation_pct if alert_type == "rise" else -deviation_pct,
                    "timestamp_detection": datetime.now().isoformat(),
                    "data_point": price['close'],
                    "full_record": json.dumps(price),
                    "details": {
                        "sma": sma,
                        "deviation_pct": deviation_pct,
                        "deviation_threshold": DEVIATION_THRESHOLD_PERCENT
                    }
                }
                es.index(index="anomalies_test", document=anomaly_document)
                anomaly_manager.process_anomaly(anomaly_document) # Process anomaly for email alerts
                producer.send("alerts", value=message)
                producer.flush()
                return f"{'🟩' if alert_type == 'rise' else '🟥'} ALERT : Price {price['close']} has deviated significantly from SMA and sent to alerts topic"
        
        return f"💹 Price {price['close']} is within normal SMA range."
