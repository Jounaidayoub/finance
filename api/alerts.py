from elasticsearch import Elasticsearch

# from airflow_ import tasks____
# import generate 


# import os


def get_anomalies(start_date, end_date, client=None):
    
    if client is None:
        client = Elasticsearch(
            hosts=["http://localhost:9200"],
            
        )
    """Get anomalies from Elasticsearch within a date range.
    note: The date format should be in ISO 8601 format.
    example:
    2025-04-01T00:00:00
    """
    resp = client.search(
        index="anomalies_test",
        from_=0,
        size=10000,
        query={
            "range": {
                "timestamp": {
                    "gte": start_date,
                    "lte": end_date
                }
            }
        },
    )
    
    return resp






# print(get_anomalies("2025-05-14T05:00:00.000Z","now"))