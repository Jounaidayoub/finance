from celery import Celery
import json
from redis import Redis
from datetime import datetime


from celery import Celery
import json
from redis import Redis
from datetime import datetime

import os
from google import genai
# from airflow_ import tasks____
# import generate 
from src.processing.reporting import get_anomalies,get_elastic_docs,get_elastic_raw_data_with_scroll,  ReportData, ReportFactory, FORMAT
from src.processing.reporting import make_PDF
from src.processing.Connection import Connection
from src.processing.detection_factory import DetectionAlgorithmFactory
from src.alerting.email_service import send_alert_email
# from json import dumps
# import json
# from datetime import datetime
# from elasticsearch import Elasticsearch




 

# redis=Redis(host='localhost', port=6379, db=0, decode_responses=True)
app = Celery("tasks",
             broker="redis://localhost:6379/0",
            backend="redis://localhost:6379/1")



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
        print(f"Error fetching anomalies: {response.status_code}")
        
        return response.json()  
    
    
    result = response.json()
    try:
        
        
        report_filename = make_PDF(result)
    except Exception as e:
        raise Exception(f"Error generating PDF report: {str(e)}")
    return report_filename
    
@app.task
def generate_and_send_report_async(from_date: str, to_date: str = None, symbol: str = None, report_format: str = "pdf", recipient_email: str = None,raw=False):
    """
    Asynchronously generates a report and sends it via email.

    Args:
        from_date (str): Start date for the report in ISO format.
        to_date (str, optional): End date for the report in ISO format. If None, current time is used.
        symbol (str, optional): Stock symbol to filter by.
        report_format (str): Format of the report (e.g., "pdf", "csv").
        recipient_email (str): Email address to send the report to.
    """
    if to_date is None:
        to_date = datetime.now().isoformat()
    print("all the paramters",from_date,to_date)
    try:
        
        # elastic_response = get_anomalies(from_date, to_date, symbol=symbol)
        if raw:
            elastic_response = get_elastic_raw_data_with_scroll(from_date, to_date, symbol=symbol,Index="raw")
        else:
            elastic_response = get_elastic_docs(from_date, to_date, symbol=symbol)
        
        anomalies = elastic_response['hits']['hits']
        if not anomalies or len(anomalies) == 0:
            print(f"No anomalies found for symbol {symbol} between {from_date} and {to_date}. Report not generated.")
            return None

        data = ReportData(
            anomalies=anomalies,
            symbol=symbol ,
            from_date=from_date,
            to_date=to_date,
        )

        generator = ReportFactory.get_report_generator(FORMAT(report_format))
        
        report_path = generator.generate_report(data) if not raw else generator.generate_raw_report(data)

        if report_path and recipient_email:
            report_type = "raw" if raw else "anomaly"
            subject = f"{report_type} Report: {from_date} to {to_date}"
            body = f"Please find attached the {report_type} report for the period {from_date} to {to_date}."
            if symbol:
                subject += f" for {symbol}"
                body += f" for symbol {symbol}."
            from time import sleep
            
            send_alert_email(subject, body, recipient=recipient_email, attachment_path=report_path, attachment_filename=os.path.basename(report_path))
            print(f"Report sent to {recipient_email}")
        elif not recipient_email:
            print("No recipient email provided. Report not sent.")
        
        return report_path

    except Exception as e:
        print(f"Error in generate_and_send_report_async: {str(e)}")
        raise

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
