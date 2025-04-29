from celery import Celery
from kafka import KafkaProducer
import json
from redis import Redis
class Producer:
    
    _prod=None
    @classmethod
    def getproducer(cls):
        if cls._prod==None:
            print("thsi whe craetaing an instacce")
            cls._prod=KafkaProducer(bootstrap_servers=['localhost:9092'],
                            value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        else:print("here it already There")
        
        
        return cls._prod
    # producer = KafkaProducer(bootstrap_servers=['localhost:9092'],
    #                          value_serializer=lambda v: json.dumps(v).encode('utf-8'))


redis=Redis(host='localhost', port=6379, db=0, decode_responses=True)
app = Celery("task",
             broker="redis://localhost:6379/0")


@app.task
def detect(price):
    producer=Producer.getproducer()
    

    
    # producer.send("alert", value=price)
    # producer.flush()
    
    redis_key="last_10"
    redis.lpush(redis_key, price[4])
    redis.ltrim(redis_key, 0, 9)
    
    
    last_10=redis.lrange(redis_key,0,-1)
    print("the last 10 prices are : ", last_10)
    
    
    max_=max(last_10)
    
    print(type(max_))
    print(type(price[4]))
    
    drop=(float(max_)- float(price[4]))/float(max_)*100
    
    if float(drop)>5:
        message=f"🟥ALERT[{drop,"%"}]: Price {price[4]} has dropped more than 5% from the last 10 prices"
        producer.send("alerts", value=message)
        producer.flush()
        return f"🟥 ALERT : Price {price} has dropped more than 5% from the last 10 prices"
    
    
    return f"💹 Price {price} is within the normal range"
    
    