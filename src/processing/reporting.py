from elasticsearch import Elasticsearch
from abc import ABC, abstractmethod
# from airflow_ import tasks____
# import generate 
from enum import Enum

from typing import Any , Optional

from pydantic import BaseModel, Field 

class FORMAT(Enum):
    """Enumeration for report formats."""
    PDF = "pdf"
    CSV = "csv"


class ReportData(BaseModel):
    """Data model for report generation."""
    anomalies: list[dict[str, Any]] = Field(..., description="List of detected anomalies")
    symbol:  Optional[str]  = Field(None, description="Stock symbol for the report")
    from_date: str = Field(..., description="Start date for the report in ISO format")
    to_date: str = Field(..., description="End date for the report in ISO format")
# import os

# making the reports service

class ReportGenerator(ABC):
    @abstractmethod
    def generate_report(self, data:ReportData):
        """Generate a report based on the provided data."""
        pass
    def generate_raw_report(self, data: ReportData):
        """"Generate a raw report from the provided data."""
        
    
class PDFReportGenerator(ReportGenerator):
    def generate_report(self, data:ReportData):
        """Generate a PDF report from the provided data."""
        return make_PDF(data)
    def generate_raw_report(self, data: ReportData):
        """
        Generate a PDF report from raw stock data (not anomalies).
        Args:
            data (ReportData): ReportData object containing raw stock data in anomalies field.
        Returns:
            str: Path to the generated PDF file.
        """
        # Placeholder for raw PDF generation logic
        raise NotImplementedError("Raw PDF report generation is not implemented yet.")

class CSVReportGenerator(ReportGenerator):
    def generate_report(self, data:ReportData):
        """Generate a CSV report from the provided data."""
        # Placeholder for CSV generation logic
        filepath=f'{data.from_date}_{data.to_date}_{data.symbol}.csv'
        try:
            
            with open(filepath,mode='a') as report:
                
                header="timestamp,symbol,price,alert_type,z_score \n"
                
                report.write(header)
                
                # write the data
                
                data.anomalies=[record["_source"] for record in data.anomalies]
                for anomaly in data.anomalies:
                    record1=f"{anomaly['timestamp']},{anomaly['symbol']},{anomaly['price']},{anomaly['alert_type']},{anomaly['details']['z_score']} \n"
                    # record=f"'timestamp': {anomaly['timestamp']}, 'open': {anomaly['open']}, 'high': {anomaly['high']}, 'low': {anomaly['low']}, 'close': {anomaly['close']}, 'volume': {anomaly['volume']}, 'symbol': all "
                    report.write(record1)
            
        except Exception as e:
            raise ValueError(f"Error while opening the file to  generate the csv ")  
                
        return filepath        
    
    def generate_raw_report(self, data: ReportData):
        """
        Generate a CSV report from raw stock data (not anomalies).
        Args:
            data (ReportData): ReportData object containing raw stock data in anomalies field.
            filepath (str): Path to save the generated CSV file.
        Returns:
            str: Path to the generated CSV file.
        """
        if data.symbol is None or data.symbol == "None":
            data.symbol = "all"
        filepath=f'{data.from_date}_{data.to_date}_{data.symbol}.csv'
        try:
            with open(filepath, mode='w') as report:
                header = "timestamp,symbol,open,high,low,close,volume\n"
                report.write(header)
                # Extract records from _source
                records = [record["_source"] for record in data.anomalies]
                for record in records:
                    row = (
                        f"{record.get('timestamp','')},"
                        f"{record.get('symbol','')},"
                        f"{record.get('open','')},"
                        f"{record.get('high','')},"
                        f"{record.get('low','')},"
                        f"{record.get('close','')},"
                        f"{record.get('volume','')}\n"
                    )
                    report.write(row)
        except Exception as e:
            raise Exception(f"Error while generating raw CSV report: {e}")
        
        return filepath
     
    
    

class ReportService:
    def __init__(self, generator: ReportGenerator):
        self.generator = generator

    def create_report(self, data: ReportData,format: str):
        """Create a report using the specified generator."""
        return self.generator.generate_report(data.model_dump())


class ReportFactory:
    #
    @staticmethod
    def get_report_generator(format: FORMAT) -> ReportGenerator:
        """Factory method to get the appropriate report generator."""
        if format == FORMAT.PDF:
            return PDFReportGenerator()
        elif format == FORMAT.CSV:
            return CSVReportGenerator()
        else:
            raise Exception(f"Unsupported report format: {format}")
        




def get_anomalies(start_date, end_date, client=None, symbol=None):
    """Get anomalies from Elasticsearch within a date range.
    
    Args:
        start_date (str): Start date in ISO format (e.g., 2025-04-01T00:00:00)
        end_date (str): End date in ISO format (e.g., 2025-05-01T00:00:00)
        client (Elasticsearch, optional): Elasticsearch client. If None, a new client is created.
        symbol (str, optional): Stock symbol to filter by
    
    Returns:
        dict: Elasticsearch response containing matching anomalies
    """
    if client is None:
        client = Elasticsearch(
            hosts=["http://localhost:9200"],
        )
    
    # Build the query
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
        query=query,
    )
    
    return resp 




def get_elastic_docs(start_date, end_date, client=None, symbol=None,Index="anomalies_test"):
    
    """Get anomalies from Elasticsearch within a date range.
    
    Args:
        start_date (str): Start date in ISO format (e.g., 2025-04-01T00:00:00)
        end_date (str): End date in ISO format (e.g., 2025-05-01T00:00:00)
        client (Elasticsearch, optional): Elasticsearch client. If None, a new client is created.
        symbol (str, optional): Stock symbol to filter by
        Indxe if not provide we will look for anomalies
    
    Returns:
        dict: Elasticsearch response containing matching anomalies
    """
    if client is None:
        client = Elasticsearch(
            hosts=["http://localhost:9200"],
        )
    
    # Build the query
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
        index=Index,
        from_=0,
        size=10000,
        query=query,
    )
    
    return resp 


def get_elastic_raw_data_with_scroll(start_date, end_date, client=None, symbol=None, Index="raw_data_index", scroll_timeout="2m"):
    """
    Get raw data from Elasticsearch within a date range using the scroll API for large datasets.

    Args:
        start_date (str): Start date in ISO format (e.g., 2025-04-01T00:00:00)
        end_date (str): End date in ISO format (e.g., 2025-05-01T00:00:00)
        client (Elasticsearch, optional): Elasticsearch client. If None, a new client is created.
        symbol (str, optional): Stock symbol to filter by
        Index (str): The Elasticsearch index to search in. Defaults to "raw_data_index".
        scroll_timeout (str): How long the scroll context should be maintained. Defaults to "2m".

    Returns:
        dict: Elasticsearch response containing all matching documents, mimicking the structure of get_elastic_docs.
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

    all_hits = []
    scroll_id = None
    total_hits = 0

    # Initial search request with scroll
    response = client.search(
        index=Index,
        scroll=scroll_timeout,
        query=query,
        size=10000 # Fetch 10,000 documents per scroll
    )

    while True:
        scroll_id = response.get('_scroll_id')
        hits = response.get('hits', {}).get('hits', [])
        total_hits = response.get('hits', {}).get('total', {}).get('value', 0) # Get total hits from initial response

        if not hits:
            break
        
        all_hits.extend(hits)

        # Continue scrolling
        response = client.scroll(
            scroll_id=scroll_id,
            scroll=scroll_timeout
        )

    # Clear the scroll context
    if scroll_id:
        client.clear_scroll(scroll_id=scroll_id)

    # Format the output to match get_elastic_docs
    return {
        "took": response.get("took", 0),
        "timed_out": response.get("timed_out", False),
        "_shards": response.get("_shards", {}),
        "hits": {
            "total": {
                "value": total_hits,
                "relation": "eq"
            },
            "max_score": response.get("hits", {}).get("max_score"),
            "hits": all_hits
        }
    }


# print(get_anomalies("2025-05-14T05:00:00.000Z","now"))













from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os

from io import BytesIO
from datetime import datetime
def make_PDF(data:ReportData):
    """
    Generate a PDF report from the provided data.
    Args:
        data (dict): Data containing anomalies and metadata for the report.
                      Expected keys: 'anomalies', 'symbol', 'from', 'to'.
    Returns:
        str: Path to the generated PDF file.
    """
    
    symbol = data.symbol
    
    start_date = data.from_date
    end_date = data.to_date
    
    
    
    # Create an absolute path 
    report_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'reports'))
    os.makedirs(report_dir, exist_ok=True)

    # generate filename
    file_suffix = f"_{symbol}" if symbol else ""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    pdf_filename = f"{report_dir}/anomaly_report{file_suffix}_{timestamp}.pdf"

    # Create the pdf document
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=landscape(letter),
        title=f"Stock Anomaly Report: {start_date} to {end_date}",
        author="Anomalies service",
        subject=f"Stock Price Anomalies: {start_date} to {end_date}",
        keywords="stocks, anomalies, analytics"
    )

   
    styles = getSampleStyleSheet()

    
    styles.add(ParagraphStyle(name='CompanyName',
                            fontName='Helvetica-Bold',
                            fontSize=16,
                            alignment=1)) 
                            
    styles.add(ParagraphStyle(name='ContactInfo',
                            fontName='Helvetica',
                            fontSize=9,
                            alignment=1,
                            textColor=colors.darkblue))

   
    elements = []


        
    # Add company header
    elements.append(Paragraph("Finance Anomalies.", styles['CompanyName']))
    elements.append(Paragraph("Financial Anomaly Detection Service", styles['Heading2']))
    elements.append(Paragraph("Email: contact@finance.com | Phone: +1 1234560000", styles['ContactInfo']))

    # Add a line
    elements.append(Spacer(1, 20))

    # Add title
    title_text = f"Stock Anomaly Detection Report for {'All stocks' if symbol is None else symbol}"
    title = Paragraph(title_text, styles['Title'])
    elements.append(title)

    # Add date range
    date_text = Paragraph(f"Period: {start_date} to {end_date}", styles['Normal'])
    elements.append(date_text)

    # Add symbol if provided
    if symbol:
        symbol_text = Paragraph(f"Symbol: {symbol}", styles['Normal'])
        elements.append(symbol_text)
        
    elements.append(Spacer(1, 20))

    # Extract anomalies from API response
    # print(data)
    try:
        # print(anomalies)
        # print(f"Extracted {len(anomalies)} anomalies from the data.")
        # print(data)
        anomalies = [anomaly['_source'] for anomaly in data.anomalies]
    except Exception as e:
        print(f"Error extracting anomalies: {e}")
        raise Exception("Invalid data format for anomalies extraction")
    # print("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh")
    # Add summary statistics
    summary_text = Paragraph(f"Total Anomalies Detected: {len(anomalies)}", styles['Heading2'])
    elements.append(summary_text)
    elements.append(Spacer(1, 10))

    # color rows based on drop/rise percentage
    if anomalies:
        headers = ["Timestamp", "Symbol", "Price", "Alert Type", "Change %", "Z-Score", "Mean", "Std Dev"]
        data = [headers]
        row_colors = []
        for anomaly in anomalies:
            timestamp = anomaly.get('timestamp', 'N/A')
            if timestamp != 'N/A':
                timestamp = timestamp.replace('T', ' ').split('.')[0]
            change_pct = anomaly.get('change_pct', 0)
            alert_type = anomaly.get('alert_type', 'N/A')
            row = [
                timestamp,
                anomaly.get('symbol', 'N/A'),
                anomaly.get('price', 'N/A'),
                alert_type,
                f"{change_pct:+.2f}%" if change_pct is not None else 'N/A',
                f"{anomaly.get('details', {}).get('z_score', 'N/A'):.2f}" if anomaly.get('details', {}).get('z_score') is not None else 'N/A',
                f"{anomaly.get('details', {}).get('mean', 'N/A'):.2f}" if anomaly.get('details', {}).get('mean') is not None else 'N/A',
                f"{anomaly.get('details', {}).get('std_dev', 'N/A'):.2f}" if anomaly.get('details', {}).get('std_dev') is not None else 'N/A'
            ]
            data.append(row)
            # Color: red for drop, green for rise
            if isinstance(change_pct, str):
                try:
                    change_pct = float(change_pct.replace('%',''))
                except:
                    change_pct = 0
            if change_pct < 0:
                row_colors.append('red')
            elif change_pct > 0:
                row_colors.append('green')
            else:
                row_colors.append(None)
        table = Table(data, repeatRows=1)
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
        ])
        # Color rows based on drop/rise
        for idx, color in enumerate(row_colors, start=1):
            if color == 'red':
                table_style.add('BACKGROUND', (0, idx), (-1, idx), colors.red)
            elif color == 'green':
                table_style.add('BACKGROUND', (0, idx), (-1, idx), colors.limegreen)
        table.setStyle(table_style)
        elements.append(table)
    else:
        # No anomalies found
        no_data_text = Paragraph("No anomalies were detected during this period.", styles['Normal'])
        elements.append(no_data_text)

    # Add timestamp of report generation
    elements.append(Spacer(1, 30))
    generation_time = Paragraph(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                            styles['Italic'])
    elements.append(generation_time)



    #buidl the final doc
    doc.build(elements)

    print(f"PDF report generated: {pdf_filename}")
    
    
    return pdf_filename
