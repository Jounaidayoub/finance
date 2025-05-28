from celery import Celery
import json
from redis import Redis
from datetime import datetime


from google import genai
# from airflow_ import tasks____
# import generate 
from reporting import get_anomalies

import os
from Connection import Connection
# from json import dumps
# import json
# from datetime import datetime
# from elasticsearch import Elasticsearch




 

# redis=Redis(host='localhost', port=6379, db=0, decode_responses=True)
app = Celery("tasks",
             broker="redis://localhost:6379/0")



# es=Elasticsearch("http://localhost:9200")


@app.task
def detect(price):
    producer=Connection.getproducer()
    

    redis=Connection.get_redis()
    redis_key="last_10_prices"
    redis.lpush(redis_key, price[4])
    redis.ltrim(redis_key, 0, 9)
    
    
    last_10=redis.lrange(redis_key,0,-1)
    print("the last 10 prices are : ", last_10)
    
    print(last_10)
    max_=max(last_10)
    
    print(type(max_))
    print(type(price[4]))
    
    drop=(float(max_)- float(price[4]))/float(max_)*100
    
   
    window=last_10
    ##calcualte the mean 
    mean=sum(float(x) for x in window)/len(window)
    
    ##calculate the standar deviation
    std=(sum(((float(x)-mean)**2 for x in window))/len(window))**(1/2)
    
    
    z_score=(float(price[4])-mean)/std

    
    # z_score=z_score(price[4],last_10)
    # z_score=/
    
    
    
    
    if abs(z_score)>2.5:
        message=f"🟥ALERT[{drop,"%"}]: Price {price[4]} has a high z_score {z_score}"
        # from elasticsearch import Elasticsearch
        # from datetime import datetime
        # es=Elasticsearch("http://localhost:9200",
        #              # http_auth=("elastic", "password"),
        #              )
        es=Connection.get_elasticsearch()
        formatted_date=datetime.strptime(price[0], "%Y-%m-%d %H:%M:%S")
        es.index(index="anomalies_test", document={
            "symbol": "TSLA",
            "price": price[4],
            "timestamp": formatted_date.isoformat(),
            "alert_type": "drop",
            "drop_percentage": drop,
            "timestamp_detection": datetime.now().isoformat(),
            "data_point": price[4],
            "full_record": price,
            "details": {
                "z_score": z_score,
                "mean": mean,
                "std_dev": std
            }
        })
        producer.send("alerts", value=message)
        
    
        producer.flush()
        return f"🟥 ALERT : Price {price} has been sent to the alerts toc"
    
    
    
    return f"💹 Price {price[4]} is within the normal range , the Z_score : {z_score}"
    
# @app.
    
@app.task
def generate_report():
    result=get_anomalies("2025-04-01T00:00:00", datetime.now().isoformat(), client=Connection.get_elasticsearch())
    print("the result is :", result)
    # from google import genai

    client = genai.Client(api_key="")

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"generate a report from the following data:{result.body}",
    )

    
    with open(f"reprort/report_{datetime.now()}.txt", "w") as f:
      f.write(response.text)
    
    print("the report has been generated")
    
    
    
app.conf.beat_schedule = {
    'write-json-every-minute': {
        'task': 'tasks.generate_report',
        'schedule': 30.0,  # seconds
    },
}