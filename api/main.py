from typing import Union
from fastapi import FastAPI, Query, Response, HTTPException
from fastapi.responses import FileResponse
import os
import sys



# Add the project root to sys.path to import from src.processing
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/processing')))
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src/processing')))
from ..src.processing.reporting import ReportService,ReportFactory,ReportGenerator,FORMAT,ReportData

# Import the alerts module and the generate_report task from tasks
from .alerts import get_anomalies
from src.processing.tasks import generate_and_send_report_async, app as celery_app

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


@app.get("/reports")
def get_report(from_: str=Query(alias="from"), to: str=Query(alias="to",default=None), symbol: str=None,format: str="pdf"):
    """
    Generate a report of anomalies within the specified date range.
    
    - **from**: Start date in ISO format (e.g., 2025-04-01T00:00:00)
    - **to**: End date in ISO format (e.g., 2025-05-01T00:00:00)
    - **symbol**: Optional stock symbol to filter by (e.g., TSLA)
    - **format**: Report format (default is "pdf")
    
    Returns:
        bytes: Generated report file in the specified format.
    """
    
    try:
        # Call the generate_report task
        elastic_response = get_anomalies(from_, to, symbol=symbol)
        anomalies = elastic_response['hits']['hits']
        if not anomalies or len(anomalies) == 0:
            raise HTTPException(
                status_code=404,    
                detail=f"No anomalies found for symbol {symbol} between {from_} and {to}"
            )
     
        
        data=ReportData(
            anomalies=elastic_response['hits']['hits'],
            symbol=symbol,
            from_date=from_,
            to_date=to,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching anomalies from Elasticserhc: {str(e)}")
    
    try:
        
        Generator= ReportFactory.get_report_generator(FORMAT(format))
        
        repoort=Generator.generate_report(data)
        
        
    except Exception as e:
        raise HTTPException(status_code=500,detail="error while generating the report "+str(e))
        
    if repoort:
        return FileResponse(
            path=repoort, 
            media_type="application/pdf",
            filename=os.path.basename(repoort),
            headers={"Content-Disposition": f"attachment; filename={os.path.basename(repoort)}"}
        )
    else:
        raise HTTPException(status_code=404, detail="Report generation failed or file not found")
        
@app.post("/reports/send_async")
def send_report_async(
    from_: str = Query(alias="from"),
    to: str = Query(alias="to", default=None),
    symbol: str = None,
    format: str = "pdf",
    recipient_email: str = Query(..., alias="recipient_email")
):
    """
    Triggers an asynchronous report generation and sending task.

    - **from**: Start date in ISO format (e.g., 2025-04-01T00:00:00)
    - **to**: End date in ISO format (e.g., 2025-05-01T00:00:00)
    - **symbol**: Optional stock symbol to filter by (e.g., TSLA)
    - **format**: Report format (default is "pdf")
    - **recipient_email**: Email address to send the report to

    Returns:
        dict: A dictionary containing the Celery task ID.
    """
    try:
        task = generate_and_send_report_async.delay(
            from_date=from_,
            to_date=to,
            symbol=symbol,
            report_format=format,
            recipient_email=recipient_email
        )
        return {"task_id": task.id, "message": "Report generation and sending task initiated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate report task: {str(e)}")

@app.post("/v1/reports")
def create_report_unified(
    from_: str = Query(alias="from"),
    to: str = Query(alias="to", default=None),
    symbol: str = None,
    format: str = "pdf",
    recipient_email: Union[str, None] = Query(default=None, alias="recipient_email")
):
    """
    Unified endpoint for generating and optionally sending reports.

    - **from**: Start date in ISO format (e.g., 2025-04-01T00:00:00)
    - **to**: End date in ISO format (e.g., 2025-05-01T00:00:00)
    - **symbol**: Optional stock symbol to filter by (e.g., TSLA)
    - **format**: Report format (default is "pdf")
    - **recipient_email**: Optional email address to send the report to. If provided, the report is sent asynchronously via email.

    Returns:
        dict or FileResponse: A dictionary with task_id if sent asynchronously, or the report file if generated synchronously.
    """
    if recipient_email:
        try:
            task = generate_and_send_report_async.delay(
                from_date=from_,
                to_date=to,
                symbol=symbol,
                report_format=format,
                recipient_email=recipient_email
            )
            return {"task_id": task.id, "message": "Asynchronous report generation and sending task initiated."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initiate asynchronous report task: {str(e)}")
    else:
        # Existing synchronous report generation logic
        try:
            elastic_response = get_anomalies(from_, to, symbol=symbol)
            anomalies = elastic_response['hits']['hits']
            if not anomalies or len(anomalies) == 0:
                raise HTTPException(
                    status_code=404,    
                    detail=f"No anomalies found for symbol {symbol} between {from_} and {to}"
                )
            
            data = ReportData(
                anomalies=elastic_response['hits']['hits'],
                symbol=symbol,
                from_date=from_,
                to_date=to,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching anomalies from Elasticsearch: {str(e)}")
        
        try:
            Generator = ReportFactory.get_report_generator(FORMAT(format))
            report = Generator.generate_report(data)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail="Error while generating the report: " + str(e))
            
        if report:
            return FileResponse(
                path=report, 
                media_type="application/pdf" if format == "pdf" else "text/csv", # Adjust media type based on format
                filename=os.path.basename(report),
                headers={"Content-Disposition": f"attachment; filename={os.path.basename(report)}"}
            )
        else:
            raise HTTPException(status_code=404, detail="Report generation failed or file not found")

@app.get("/v1/reports/status/{task_id}")
def get_report_task_status(task_id: str):
    """
    Retrieves the status of an asynchronous report generation task.

    - **task_id**: The ID of the Celery task.

    Returns:
        dict: A dictionary containing the task's status and result (if available).
    """
    task = celery_app.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'task_id': task.id,
            'status': task.state,
            'message': 'Task is pending or not found.'
        }
    elif task.state == 'FAILURE':
        response = {
            'task_id': task.id,
            'status': task.state,
            'result': str(task.result),
            'message': 'Task failed.'
        }
    else:
        response = {
            'task_id': task.id,
            'status': task.state,
            'result': task.result
        }
    return response

@app.get("/reports/pdf")
def get_pdf_report(from_: str=Query(alias="from"), to: str=Query(alias="to",default=None), symbol: str=None):
    """
       **DEPRECATED**: Use /reports?format=pdf instead.
       
    Generate and return a PDF report of anomalies within the specified date range.
    
    - **from**: Start date in ISO format (e.g., 2025-04-01T00:00:00)
    - **to**: End date in ISO format (e.g., 2025-05-01T00:00:00)
    - **symbol**: Optional stock symbol to filter by (e.g., TSLA)
    
    Returns:
        PDF file containing a report of the anomalies
    """
    
    format = "pdf"
    try:
        
        # generator= ReportFactory.get_report_generator(format)
        
        # generator.generate_report()
        
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
