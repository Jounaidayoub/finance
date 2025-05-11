from celery import Celery
from kafka import KafkaProducer
import json
from redis import Redis
from datetime import datetime
from elasticsearch import Elasticsearch


class Producer:
    
    _prod=None
    _elasticsearch=None
    @classmethod
    def getproducer(cls):
        if cls._prod==None:
            print("thsi whe craetaing an instacce")
            cls._prod=KafkaProducer(bootstrap_servers=['localhost:9092'],
                            value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        else:print("here it already There")
        
        
        return cls._prod
    
    # @classmethod
    
        
    #     return cls._prod
    # # producer = KafkaProducer(bootstrap_servers=['localhost:9092'],
    # #                          value_serializer=lambda v: json.dumps(v).encode('utf-8'))


redis=Redis(host='localhost', port=6379, db=0, decode_responses=True)
app = Celery("tasks",
             broker="redis://localhost:6379/0")



es=Elasticsearch("http://localhost:9200")


@app.task
def detect(price):
    producer=Producer.getproducer()
    

   
    redis_key="last_10"
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
        """
        {
  "mappings": {
    "properties": {
      "data_point": {
        "type": "float"
      },
      "details": {
        "type": "nested"
      },
      "full_record": {
        "type": "text"
      },
      "symbol": {
        "type": "keyword"
      },
      "timestamp": {
        "type": "date"
      },
      "timestamp_detection": {
        "type": "date"
      },
      "type": {
        "type": "keyword"
      }
    }
  }
}"""
        es.index(index="alerts", document={
            "symbol": price[0],
            "price": price[4],
            "timestamp": datetime.now().isoformat(),
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
    
