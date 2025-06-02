from elasticsearch import Elasticsearch
import os
import sys
from datetime import datetime

# Add the src directory to the path so we can import the necessary modules if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Ensure the path is properly set up for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def get_anomalies(start_date, end_date, client=None, symbol=None):
    """
    Get anomalies from Elasticsearch within a date range.
    
    Args:
        start_date (str): Start date in ISO format (e.g., 2025-04-01T00:00:00)
        end_date (str): End date in ISO format (e.g., 2025-05-01T00:00:00)
        client (Elasticsearch, optional): Elasticsearch client. If None, a new client is created.
        symbol (str, optional): Stock symbol to filter by
        
    Returns:
        dict: Elasticsearch response containing matching anomalies
    
    Note: The date format should be in ISO 8601 format.
    Example: 2025-04-01T00:00:00
    """
    if client is None:
        client = Elasticsearch(
            hosts=["http://localhost:9200"],
        )
    
    query = {
            "bool": {
                "must": [
                    {   
                        
                    
                        "range": {
                            "timestamp": {
                                "gte": start_date,
                                "lte": end_date
                            }
                        }
                    }
                ]
            }
        }
    if symbol:
        query["bool"]["must"].append({
            "match": {
                "symbol": symbol
            }
        })
    resp = client.search(
        index="anomalies_test",
        from_=0,
        size=10000,
        query=query
    )
    
    return resp

def generate_pdf_report(start_date, end_date, symbol=None):
    """
    Generate a PDF report for anomalies within the specified date range.
    
    Args:
        start_date (str): Start date in ISO format
        end_date (str): End date in ISO format
        symbol (str, optional): Stock symbol to filter by
    
    Returns:
        str: Path to the generated PDF file
    """
    from src.processing.tasks import generate_report
    
    try:
        # Call the generate_report task synchronously
        pdf_path = generate_report(start_date, end_date, symbol=symbol)
        return pdf_path
    except Exception as e:
        print(f"Error generating PDF report: {str(e)}")
        raise e

# print(get_anomalies("2025-05-14T05:00:00.000Z","now"))