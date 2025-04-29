from kafka import KafkaConsumer
import json

# asd
consumer = KafkaConsumer(
    'alerts',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),)

for message in consumer:
    print("Received alert:", message.value)
    # Process the message as needed
    # For example, you can print the data or perform any other operations
    # print(message.value)
