# Data engineering project
## Description
This mini project was part of the *Data Engineering* course of the *Internationale Hochschule (IU)*. The goal was to implement a storage pipeline for a continuous datastream. As data source I chose the accelerometer sensor in my smartphone. The [Sensor Server](https://github.com/umer0586/SensorServer) application, part of the [F-Droid](https://f-droid.org/en/about/) app repository, allowed me to access my smartphone's sensor data. [Apache Kafka](https://kafka.apache.org/intro) was chosen as message queue, connecting my smartphone and the database. The Document database MongoDB was chosen for the latter. I packaged the whole pipeline as a container stack using Docker Compose.

## Prerequisites
1. The latest versions of Docker and Docker Compose are installed on your system.
2. You are in the project's root directory, e.g. on Linux /home/user/data_engineering/.
3. You have an Android smartphone with F-Droid installed ([Installation instructions](https://f-droid.org/en/docs/Get_F-Droid/#option-2-download-and-install-f-droid-apk)).
4. You have installed [Sensor Server](https://f-droid.org/en/packages/github.umer0586.sensorserver/) through the F-Droid app.
5. Your phone with the *SensorServer* app is on the same local network as the computer running the container stack.
6. Your *Sensor Server* is discoverable on your local network. (In the app: Hamburger menu in the top-left corner => Settings => Discoverable (last option)).

## Configuration
The streaming data pipeline was designed to work with minimal human intervention and maximum convenience. The `ZeroconfListener` class in the [publisher python script](publisher/publisher.py) attempts to find your *Sensor Server* on the local network. However, on my network this did not work right out of the box (I'm using a Fritzbox router). If the *container stack* has trouble finding the *Sensor Server* on your network, please manually define the `SENSOR_HOSTNAME` environment variable in the [docker-compose.yml](docker-compose.yml) file. The correct `SENSOR_HOSTNAME` is displayed in the *Sensor Server* app after tapping the *START* button: `ws://SENSOR_HOSTNAME:8080`. Note that if the `SENSOR_HOSTNAME` environment variable is left empty, zeroconf will default to looking for the *Sensor Server* automatically.

## Usage
- Build the container images and start all services with `docker compose up --build -d`.
- Verify operation of the publisher with `docker compose logs -f publisher`.
```bash
Example output:
publisher-1  | Kafka broker at kafka:9092 not available. Retrying in 5 seconds...
publisher-1  | Kafka broker at kafka:9092 not available. Retrying in 5 seconds...
publisher-1  | Kafka broker at kafka:9092 not available. Retrying in 5 seconds...
publisher-1  | Kafka producer connected.
publisher-1  | Publisher script starting...
publisher-1  | SENSOR_HOSTNAME environment variable set to 'Android.fritz.box'. Bypassing Zeroconf discovery.
publisher-1  | Attempting to connect to SensorServer at ws://Android.fritz.box:8080/sensor/connect?type=android.sensor.accelerometer
publisher-1  | WebSocket connection opened.
publisher-1  | Sent to Kafka: {'values': [0.0049500004, -0.24495001, 9.876], 'timestamp': 2954659628160233, 'accuracy': 3}
publisher-1  | Sent to Kafka: {'values': [-0.003, -0.24300002, 9.868951], 'timestamp': 2954659708447579, 'accuracy': 3}
publisher-1  | Sent to Kafka: {'values': [0.003, -0.23805001, 9.876], 'timestamp': 2954659788727924, 'accuracy': 3}
```
- Verify operation of the subscriber with `docker compose logs -f subscriber`.
```bash
Example output:
subscriber-1  | Subscriber service starting...
subscriber-1  | Kafka broker at kafka:9092 not available. Retrying in 5 seconds...
subscriber-1  | Kafka broker at kafka:9092 not available. Retrying in 5 seconds...
subscriber-1  | Kafka broker at kafka:9092 not available. Retrying in 5 seconds...
subscriber-1  | Kafka consumer connected.
subscriber-1  | Attempting to connect to MongoDB...
subscriber-1  | MongoDB client connected.
subscriber-1  | Listening for messages on Kafka topic 'sensor-data'...
```
- Access the stored accelerometer data with:
```bash
docker compose exec mongodb mongosh
use admin
db.auth('root', 'example')
use sensordata
db.accelerometer.find().limit(5).pretty()
```
- Stop all the running containers without deleting any data with `docker compose down`.

OR

- Stop the running containers AND delete all the sensor data stored in MongoDB with `docker compose down -v`.
