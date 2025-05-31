import subprocess
import csv
import os
from time import sleep
# from playsound import playsound
import os
from kafka import KafkaProducer
import json


csv_file_path = 'NFLX_1min_sample.csv'

producer = KafkaProducer(bootstrap_servers='localhost:9092',
                         value_serializer=lambda v: json.dumps(v).encode('utf-8'))

with open(csv_file_path, 'r') as csvfile:
    reader = csv.reader(csvfile)
    header = next(reader)  # Skip the header row
    cleaned_header = [h.strip() for h in header]  # Clean header names
    data = [dict(zip(cleaned_header,row)) for row in reader]

# print(data, end='\n')
# print each minute a new line of data
# ['timestamp', 'open', 'high', 'low', 'close', 'volume'].
prev = 0

for i in range(len(data)):
    diff = float(data[i]['open']) - prev

    # if abs(diff) > 1.5:
    #     os.system("echo -ne '\007'")
    #     subprocess.run(["echo", "-ne", "\\007"], shell=True)
    #     # print('\a')
    #     # print("ALERT!")
    # else:
    #     print("       ", end='\n')
    
    data[i]['symbol'] = 'NFXL'
    producer.send('tsla-data', value=[data[i], diff])
    # if abs(diff) > 1.5:
    #     producer.send('alert', value=diff)

    # print("Sending data to Kafka topic 'stock_data'")
    print("Data sent:", data[i], end='\n')
    # print(data[i],"diff:", diff,end='\n')
    prev = float(data[i]['open'])
    prev = round(prev, 2)
    # data[i]['symbol'] ='TSLA' 
    # print(data[i])
    sleep(1/100000)  # Sleep for 1 minute between each line of data
    # os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console for the next line

producer.flush()
