from elasticsearch import Elasticsearch
from kafka import KafkaProducer
from redis import Redis
import json
class Connection:
    
    _prod=None
    _elasticsearch=None
    _redis=None
    @classmethod
    def getproducer(cls):
        if cls._prod==None:
            print("thsi whe craetaing an instacce")
            cls._prod=KafkaProducer(bootstrap_servers=['localhost:9092'],
                            value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        else:print("here it already There")
        
        
        return cls._prod
    
    @classmethod
    def get_elasticsearch(cls):
        if cls._elasticsearch==None:
            # print("thsi whe craetaing an instacce")
            cls._elasticsearch=Elasticsearch(
                hosts=["http://localhost:9200"],
                
            )
        # else:print("here it already There")
        
        
        return cls._elasticsearch
    @classmethod
    def get_redis(cls):
        if cls._redis==None:
            # print("thsi whe craetaing an instacce")
            cls._redis=Redis(host='localhost', port=6379, db=0, decode_responses=True)
        # else:print("here it already There")
        
        
        return cls._redis
       