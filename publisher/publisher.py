import json
import os
import socket
import threading
import time
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import websocket
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

KAFKA_TOPIC = "sensor-data"
KAFKA_BROKER = "kafka:9092"
SENSOR_PORT = 8080
SENSOR_TYPE = "android.sensor.accelerometer"

def create_kafka_producer():
    """Creates a Kafka producer, retrying until a connection is established."""
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("Kafka producer connected.", flush=True)
            return producer
        except NoBrokersAvailable:
            print(f"Kafka broker at {KAFKA_BROKER} not available. Retrying in 5 seconds...", flush=True)
            time.sleep(5)

producer = create_kafka_producer()

def on_message(ws, message):
    try:
        data = json.loads(message)
        producer.send(KAFKA_TOPIC, data)
        print(f"Sent to Kafka: {data}", flush=True)
    except Exception as e:
        print(f"An error occurred in on_message: {e}", flush=True)

def on_error(ws, error):
    print(f"WebSocket error: {error}", flush=True)

def on_close(ws, close_code, reason):
    print(f"WebSocket connection closed: {close_code} - {reason}", flush=True)

def on_open(ws):
    print("WebSocket connection opened.", flush=True)

def connect_and_publish(url):
    """Connects to the WebSocket and retries on failure."""
    print(f"Attempting to connect to SensorServer at {url}", flush=True)
    while True:
        ws = websocket.WebSocketApp(url, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.run_forever()
        print("Connection lost. Retrying in 10 seconds...", flush=True)
        time.sleep(10)

class ZeroconfListener(ServiceListener):
    """Service listener for Zeroconf discovery."""
    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info and name == "SensorServer":
            address = socket.inet_ntoa(info.addresses[0])
            url = f"ws://{address}:{info.port}/sensor/connect?type={SENSOR_TYPE}"
            print(f"Found SensorServer via Zeroconf at {url}", flush=True)
            threading.Thread(target=connect_and_publish, args=(url,), daemon=True).start()
            # We can close zeroconf now that we've found the service.
            zc.close()

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None: pass
    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None: pass

if __name__ == "__main__":
    print("Publisher script starting...", flush=True)
    hostname = os.environ.get('SENSOR_HOSTNAME')

    if hostname:
        # --- Manual Hostname Mode ---
        print(f"SENSOR_HOSTNAME environment variable set to '{hostname}'. Bypassing Zeroconf discovery.", flush=True)
        url = f"ws://{hostname}:{SENSOR_PORT}/sensor/connect?type={SENSOR_TYPE}"
        connect_and_publish(url)
    else:
        # --- Automatic Zeroconf Discovery Mode ---
        print("SENSOR_HOSTNAME not set. Starting Zeroconf discovery...", flush=True)
        zeroconf = Zeroconf()
        listener = ZeroconfListener()
        browser = ServiceBrowser(zeroconf, "_websocket._tcp.local.", listener)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping...", flush=True)
        finally:
            zeroconf.close()