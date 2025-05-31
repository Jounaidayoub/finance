echo "activating the virtual environment"
source venv/bin/activate
echo "starting the consumers"
python3 src/processing/consumer.py 
echo "staring the Celery worker"
cd src/processing && celery -A tasks worker --loglevel=info --logfile=celery.log &
celery -A tasks flower --loglevel=info --logfile=celery_flower.log &

# echo "starting the FastApi server"
# echo $(pwd)
# cd ../api && fastapi dev main.py
# echo $(pwd)


# echo "now trigger the generation of the data"
# cd ../src/data_generator && python3 generator.py & python3 generator_1.py & python3 generator_2.py & python3 generator_3.py &