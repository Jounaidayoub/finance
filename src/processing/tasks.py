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
from detection_factory import DetectionAlgorithmFactory
# from json import dumps
# import json
# from datetime import datetime
# from elasticsearch import Elasticsearch




 

# redis=Redis(host='localhost', port=6379, db=0, decode_responses=True)
app = Celery("tasks",
             broker="redis://localhost:6379/0")



# es=Elasticsearch("http://localhost:9200")


@app.task
def detect(price, algorithm_type="z_score"):
    detector = DetectionAlgorithmFactory.get_algorithm(algorithm_type)
    return detector.detect(price)
    
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
