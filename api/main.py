from typing import Union
from fastapi import FastAPI,Query
# from src.processing.reporting import get_anomalies
from alerts import get_anomalies
app = FastAPI()














@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/alerts")
# 
def anomalies(from_: str=Query(alias="from"), to: str=Query(alias="to")):
    # I use from_ because form is a python keyword , peak documentation
    return get_anomalies(from_, to)



@app.get("/alerts/{symbol}/")
def get_anomalies_by_symbol(symbol:str , from_: str=Query(alias="from"), to: str=Query(alias="to")):
    """
    Get anomalies for a specific symbol within a date range.
    """
    resp = get_anomalies(from_, to, symbol=symbol)
   
    return resp