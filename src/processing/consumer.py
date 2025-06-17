from kafka import KafkaConsumer,KafkaProducer
import json
from src.processing.tasks import detect

from src.processing.Connection import Connection
from src.processing.detection_factory import DetectionAlgorithmFactory

from src.processing.utils import put_to_index

producer = KafkaProducer(bootstrap_servers='localhost:9092',
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))


consumer = KafkaConsumer(
    'tsla-data',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
    # auto_offset_reset='earliest'
)


for message in consumer:
    
        
        
    
    # Use the factory to get the detection algorithm and then call the Celery task
    # The detect task now expects the price directly, and the factory logic is inside the task
    detect.delay(message.value[0])
    
    
    # type(detect.delay(message.value[0]))
    
    try:
        put_to_index(message.value[0],client=Connection.get_elasticsearch())
    except Exception as e:
        print(f"Error storing  row data in Elasticsearch: {str(e)}")
    
    
    # store the raw data in elasticsearch
    
    
    
    
    
    
    
    # print('\a')
    print("Received message:", message.value[0], message.value[1], "ALERT" if abs(
        message.value[1]) > 1.5 else "No Alert")
    # Process the message as needed
    # For example, you can print the data or perform any other operations
    # print(message.value)
