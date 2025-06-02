from celery import Celery
import json
from redis import Redis
from datetime import datetime


from google import genai
# from airflow_ import tasks____
# import generate 
from reporting import get_anomalies
from reporting import make_PDF
from Connection import Connection
# from json import dumps
# import json
# from datetime import datetime
# from elasticsearch import Elasticsearch




 

# redis=Redis(host='localhost', port=6379, db=0, decode_responses=True)
app = Celery("tasks",
             broker="redis://localhost:6379/0")



# es=Elasticsearch("http://localhost:9200")


@app.task
def detect(price):
    producer=Connection.getproducer()
    

    redis=Connection.get_redis()
    symbol = price.get('symbol', 'N/A')  
    redis_key=f"last_10_prices_{symbol}" # This need an invesitgation , it does 
    # show anything in redis, but it works fine in the code
    redis.lpush(redis_key, price['close'])
    redis.ltrim(redis_key, 0, 9)
    
    
    last_10=redis.lrange(redis_key,0,-1)
    
    
    print(f"Last 10 prices for {symbol}: {last_10}")
    
    # import ipdb; ipdb.set_trace()  # Breakpoint here

    # print("the last 10 prices are : ", last_10)
    
    # print(last_10)
    max_=max(last_10)
    
    # print(type(max_))
    # print(type(price['close']))
    
    # Use previous price for anomaly detection
    if len(last_10) > 1:
        prev_price = float(last_10[1])  
        curr_price = float(price.get('close', 0.0))
        change_pct = (curr_price - prev_price) / prev_price * 100
        alert_type = "rise" if change_pct > 0 else "drop"
    else:
        # Not enough data to compare
        change_pct = 0.0
        alert_type = None

    window = last_10
    ##calcualte the mean 
    mean=sum(float(x) for x in window)/len(window)
    
    ##calculate the standar deviation
    std=(sum(((float(x)-mean)**2 for x in window))/len(window))**(1/2)
    
    
    z_score=(float(price['close'])-mean)/std

    if abs(z_score) > 2.5 and alert_type:
        message = f"{price['symbol']}{'🟩' if alert_type == 'rise' else '🟥'}ALERT[{change_pct:+.2f}%]: Price {price['close']} has a high z_score {z_score}"
        es = Connection.get_elasticsearch()
        formatted_date = datetime.strptime(price['timestamp'], "%Y-%m-%d %H:%M:%S")
        es.index(index="anomalies_test", document={
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
        })
        producer.send("alerts", value=message)
        producer.flush()
        return f"{'🟩' if alert_type == 'rise' else '🟥'} ALERT : Price {price} has been sent to the alerts topic"

    return f"💹 Price {price['close']} is within the normal range , the Z_score : {z_score}"
    
# @app.
    
@app.task
def generate_report(start_date="2025-04-01T00:00:00", end_date=None, symbol=None):
    """
    Generate a PDF report containing anomalies within the specified date range.
    
    Args:
        start_date (str): Start date in ISO format
        end_date (str, optional): End date in ISO format. If None, current time is used.
        symbol (str, optional): Stock symbol to filter by
    
    Returns:
        str: Path to the generated PDF file
    """
    # if no end date is provided  use current time
    if end_date is None:
        end_date = datetime.now().isoformat()
    
    
    # get the anomalies from the api
    
    import requests
    
    
    base_url = "http://localhost:8000/alerts"
    if symbol:
        url = f"{base_url}/{symbol}/?from={start_date}&to={end_date}"
    else:
        url = f"{base_url}?from={start_date}&to={end_date}"
    
    # Make the API request
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Error fetching anomaliesss: {response.status_code}")
        
        return response.json()  
    
    
    result = response.json()
    try:
        
        report_filename = make_PDF(result)
    except Exception as e:
        raise Exception(f"Error generating PDF report: {str(e)}")
    return report_filename
    
    
    
# Configure Celery Beat schedule for automatic report generation

app.conf.beat_schedule = {
    'generate-daily-anomaly-report': {
        'task': 'tasks.generate_report',
        'schedule': 86400.0,  
        # 'schedule': 5,  
        'kwargs': {
            'start_date': "now-1d",  # Starting from a fixed date
            
        }
    },
}