from typing import Union
from fastapi import FastAPI, Query, Response, HTTPException
from fastapi.responses import FileResponse
import os
import sys

# Add the project root to sys.path to import from src.processing
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/processing')))

# Import the alerts module and the generate_report task from tasks
from alerts import get_anomalies
from src.processing.tasks import generate_report

app = FastAPI(
    title="Stock Anomaly Detection API",
    description="API for detecting and reporting stock price anomalies",
    version="1.0.0",
    
)

@app.get("/")
def read_root():
    return {
        "name": "Stock Anomaly Detection API",
        "version": "1.0.0",
        "endpoints": [
            "/alerts - Get all anomalies",
            "/alerts/{symbol} - Get anomalies for a specific symbol",
            "/reports/pdf - Generate PDF report of anomalies"
        ]
    }

@app.get("/alerts")
def anomalies(from_: str=Query(alias="from"), to: str=Query(alias="to")):
    """
    Get all anomalies within a date range.
    
    - **from**: Start date in ISO format (e.g., 2025-04-01T00:00:00)
    - **to**: End date in ISO format (e.g., 2025-05-01T00:00:00)
    """
    
    # I used from_ because form is a python keyword, peak documentation
    try:
        result = get_anomalies(from_, to)
        analyses = result['hits']['hits']
        response={
            "from": from_,
            "to": to,
            "symbol": 'all',
            "hits": result['hits']['total']['value'],
            "anomalies": result['hits']['hits'],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching anomalies: {str(e)}")
    return response


@app.get("/alerts/{symbol}/")
def get_anomalies_by_symbol(symbol: str, from_: str=Query(alias="from"), to: str=Query(alias="to")):
    """
    Get anomalies for a specific symbol within a date range.
    
    - **symbol**: Stock symbol (e.g., TSLA)
    - **from**: Start date in ISO format (e.g., 2025-04-01T00:00:00)
    - **to**: End date in ISO format (e.g., 2025-05-01T00:00:00)
    """
    try:
        resp = get_anomalies(from_, to, symbol=symbol)
        response={
            "from": from_,
            "to": to,
            "symbol": 'all',
            "hits": resp['hits']['total']['value'],
            "anomalies": resp['hits']['hits'],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching anomalies for {symbol}: {str(e)}")
    return response

@app.get("/reports/pdf")
def get_pdf_report(from_: str=Query(alias="from"), to: str=Query(alias="to",default=None), symbol: str=None):
    """
    Generate and return a PDF report of anomalies within the specified date range.
    
    - **from**: Start date in ISO format (e.g., 2025-04-01T00:00:00)
    - **to**: End date in ISO format (e.g., 2025-05-01T00:00:00)
    - **symbol**: Optional stock symbol to filter by (e.g., TSLA)
    
    Returns:
        PDF file containing a report of the anomalies
    """
    try:
        # generate the PDF report
        pdf_path = generate_report(from_, to, symbol=symbol)
        
        if not pdf_path:
            raise HTTPException(status_code=404, detail="Report generation failed")
            
        # check if file exists
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="Generated report file not found")
            
        
        filename = os.path.basename(pdf_path)
        return FileResponse(
            path=pdf_path, 
            media_type="application/pdf",
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation error: {str(e)}")