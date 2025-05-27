from typing import Union
from fastapi import FastAPI,Query
# from src.processing.reporting import get_anomalies
from alerts import get_anomalies
app = FastAPI()














@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/alerts")
def anomalies(from_: str=Query(alias="from"), to: str=Query(alias="to")):
    
    return get_anomalies(from_, to)