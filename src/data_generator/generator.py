import subprocess
import csv
import os
from time import sleep
# from playsound import playsound
import os
from kafka import KafkaProducer
import json


csv_file_path = 'TSLA_1min_sample.csv'

producer = KafkaProducer(bootstrap_servers='localhost:9092',
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))


with open(csv_file_path, 'r') as csvfile:
    reader = csv.reader(csvfile)
    header = next(reader)  # Skip the header row
    data = [row for row in reader]

# print(data, end='\n')
# print each minute a new line of data

prev = 0

for i in range(len(data)):
    diff = float(data[i][1]) - prev

    # if abs(diff) > 1.5:
    #     os.system("echo -ne '\007'")
    #     subprocess.run(["echo", "-ne", "\\007"], shell=True)
    #     # print('\a')
    #     # print("ALERT!")
    # else:
    #     print("       ", end='\n')
    producer.send('tsla-data', value=[data[i], diff])
    # if abs(diff) > 1.5:
    #     producer.send('alert', value=diff)

    # print("Sending data to Kafka topic 'stock_data'")
    print("Data sent:", data[i], end='\n')
    # print(data[i],"diff:", diff,end='\n')
    prev = float(data[i][1])
    prev = round(prev, 2)
    sleep(1)  # Sleep for 1 minute between each line of data
    # os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console for the next line

producer.flush()
