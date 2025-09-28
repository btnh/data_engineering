import json
import os
import time
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

KAFKA_TOPIC = "sensor_data"
KAFKA_BROKER = "kafka:9092"
MONGO_HOST = "mongodb"
MONGO_PORT = 27017
MONGO_DB = "sensordata"
MONGO_COLLECTION = "accelerometer"

# Get MongoDB credentials from environment variables
MONGO_USERNAME = os.environ.get('MONGO_USERNAME')
MONGO_PASSWORD = os.environ.get('MONGO_PASSWORD')

def create_kafka_consumer():
    """Creates a Kafka consumer, retrying until a connection is established."""
    while True:
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC,
                bootstrap_servers=[KAFKA_BROKER],
                auto_offset_reset='earliest',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            print("Kafka consumer connected.", flush=True)
            return consumer
        except NoBrokersAvailable:
            print(f"Kafka broker at {KAFKA_BROKER} not available. Retrying in 5 seconds...", flush=True)
            time.sleep(5)

def create_mongo_client():
    """Creates a MongoDB client, retrying until a connection is established."""
    while True:
        try:
            print("Attempting to connect to MongoDB...", flush=True)
            client = MongoClient(
                host=MONGO_HOST,
                port=MONGO_PORT,
                username=MONGO_USERNAME,
                password=MONGO_PASSWORD,
                authSource='admin' # Specify the authentication database
            )
            # The ismaster command is cheap and does not require auth, but will verify the connection.
            client.admin.command('ismaster')
            print("MongoDB client connected.", flush=True)
            return client
        except ConnectionFailure as e:
            print(f"MongoDB at {MONGO_HOST}:{MONGO_PORT} not available. Error: {e}. Retrying in 5 seconds...", flush=True)
            time.sleep(5)
        except Exception as e:
            print(f"An unexpected error occurred while connecting to MongoDB: {e}. Retrying in 5 seconds...", flush=True)
            time.sleep(5)

def main():
    """Main function to consume from Kafka and write to MongoDB."""
    print("Subscriber service starting...", flush=True)
    
    consumer = create_kafka_consumer()
    mongo_client = create_mongo_client()
    db = mongo_client[MONGO_DB]
    collection = db[MONGO_COLLECTION]

    print(f"Listening for messages on Kafka topic '{KAFKA_TOPIC}'...", flush=True)
    for message in consumer:
        try:
            sensor_data = message.value
            collection.insert_one(sensor_data)
            print(f"Inserted into MongoDB: {sensor_data}", flush=True)
        except Exception as e:
            print(f"Error processing message: {message.value}. Error: {e}", flush=True)

if __name__ == "__main__":
    main()