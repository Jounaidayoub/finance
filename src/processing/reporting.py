from elasticsearch import Elasticsearch

# from airflow_ import tasks____
# import generate 


# import os


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






# print(get_anomalies("2025-05-14T05:00:00.000Z","now"))













from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os

from io import BytesIO
from datetime import datetime
def make_PDF(data):
    """
    Generate a PDF report from the provided data.
    Args:
        data (dict): Data containing anomalies and metadata for the report.
                      Expected keys: 'anomalies', 'symbol', 'from', 'to'.
    Returns:
        str: Path to the generated PDF file.
    """
    
    symbol = data.get('symbol', None)
    start_date = data.get('from')
    end_date = data.get('to')
    
    
    
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
        author="TSLA Analytics, Inc.",
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
    elements.append(Paragraph("TSLA Analytics, Inc.", styles['CompanyName']))
    elements.append(Paragraph("Financial Anomaly Detection Service", styles['Heading2']))
    elements.append(Paragraph("Email: contact@tsla-analytics.com | Phone: +1 (555) 123-4567", styles['ContactInfo']))

    # Add a line
    elements.append(Spacer(1, 20))

    # Add title
    title = Paragraph(f"Stock Anomaly Detection Report", styles['Title'])
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
        anomalies = [anomaly['_source'] for anomaly in data['anomalies']]
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