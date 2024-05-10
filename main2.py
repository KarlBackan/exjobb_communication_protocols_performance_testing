import asyncio
import json
import logging
import os
import random
import time
import uuid
from statistics import mean
from time import perf_counter
from timeit import default_timer as timer
import pandas as pd
import paho.mqtt.client as mqtt
import websockets
import warnings


samplesPerParameter = 3

# Setup detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PerformanceMetrics:
    def __init__(self, filename, scenario_description):
        self.start_time = time.time()
        self.filename = filename
        self.scenario_description = scenario_description
        self.data = pd.DataFrame(columns=[
            "Parameter", "Average Latency", "Samples", "Protocol"
        ])
        self.log_counter = 0
        logging.info(f"Starting test scenario: {scenario_description}")

    def log_message(self, parameter, protocol, latency):
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        new_data = pd.DataFrame([{
            "Parameter": parameter,
            "Average Latency": latency,
            "Samples": samplesPerParameter,
            "Protocol": protocol,
        }])

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FutureWarning)
            self.data = pd.concat([self.data, new_data], ignore_index=True)

    def save_data(self):
        if not self.data.empty:
            self.data.to_csv(self.filename, mode='a', header=not os.path.exists(self.filename), index=False)
            logging.info(f"Performance data saved to {self.filename}. Data reset.")
            self.data = pd.DataFrame(columns=self.data.columns)  # Reset the DataFrame

    async def log_performance(self):
        # This function might not be needed if you call save_data() explicitly after test runs
        while True:
            await asyncio.sleep(60)  # Example: Save every 60 seconds if needed
            self.save_data()

def linear_space(start, end, num):
    step = (end - start) / (num - 1)
    return [start + step * i for i in range(num)]

# Define scenarios
# Define scenarios with consistent keys for range values
scenarios = {
    "frequency": {"start": 0.01, "end": 1, "num_values": 10, "payload_size": 50, "description": "Varying message frequency."},
    "payload": {"start": 100, "end": 1000000, "num_values": 10, "interval": 5, "description": "Varying payload sizes."},
    #"concurrency": {"start": 1, "end": 10, "num_values": 10, "interval": 3, "description": "Varying number of clients."}
}

# Initialize metrics instances for each scenario
metrics = {}
for key, settings in scenarios.items():
    metrics[key] = PerformanceMetrics(f"{key}_performance.csv", settings['description'])

class MQTTServer:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f'python-mqtt-{random.randint(0, 1000)}', protocol=mqtt.MQTTv5)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc, properties=None):
        logging.info("MQTT Server Connected")
        client.subscribe("test/topic")

    def on_message(self, client, userdata, msg):
        data = json.loads(msg.payload.decode())
        sent_time = timer()
        unique_id = str(uuid.uuid4())
        message = json.dumps({
            "message": "X" * int(float(data["message"])),
            "sent_time": sent_time,
            "id": unique_id
        })

        data['sent_time'] = timer()  # Update or echo back the sent time
        response = json.dumps(data)
        client.publish("test/response", response)

    def start(self):
        try:
            self.client.connect("localhost", 1883, 60)  # Ensure 'localhost' is correct
            self.client.loop_start()
            logging.info("MQTT Server started and listening")
        except Exception as e:
            logging.error(f"MQTT Server failed to start: {e}")


class MQTTClient:
    def __init__(self, scenario_key, parameter):
        settings = scenarios[scenario_key]
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f'python-mqtt-{random.randint(0, 1000)}', protocol=mqtt.MQTTv5)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.parameter = parameter
        self.interval = parameter if scenario_key == 'frequency' else settings['interval']
        self.payload_size = parameter if scenario_key == 'payload' else settings['payload_size']
        self.metrics = metrics[scenario_key]
        self.latency_list = []
        self.client.connect("localhost", 1883, 60)

    def on_connect(self, client, userdata, flags, rc, properties=None):
        logging.info(f"MQTT Client Connected with RC: {rc}")
        client.subscribe("test/response")

    def on_message(self, client, userdata, msg):
        data = json.loads(msg.payload.decode())
        if 'id' in data and 'sent_time' in data:  # Make sure the message is properly formatted
            latency = timer() - data['sent_time']
            self.latency_list.append(latency)

    async def send_messages(self):
        self.client.loop_start()
        for _ in range(samplesPerParameter):
            unique_id = str(uuid.uuid4())
            message = json.dumps({
                "message": str(self.payload_size),
                "sent_time": timer(),
                "id": unique_id
            })
            self.client.publish("test/topic", message)
            await asyncio.sleep(self.interval)
        self.client.loop_stop()
        self.client.disconnect()

        # After all messages are sent and processed:
        if self.latency_list:
            average_latency = mean(self.latency_list)
            self.metrics.log_message(self.parameter, "MQTT", average_latency)
            logging.info(f"Recorded Average Latency for MQTT: {average_latency}s")


class WebSocketServer:
    def __init__(self):
        self.metrics = None
        self.parameter = None
        self.connections = set()

    def change_metrics(self, new_metrics):
        self.metrics = metrics[new_metrics]
    def change_parameter(self, new_parameter):
        self.parameter = new_parameter

    async def handle_connection(self, websocket, path):
        self.connections.add(websocket)
        try:
            while True:  # Keep connection open to handle multiple messages
                message = await websocket.recv()
                data = json.loads(message)
                unique_id = str(uuid.uuid4())  # Generate a unique identifier for each message
                message = json.dumps({
                    "message": "X" * int(float(data["message"])),
                    "sent_time": timer(),
                    "id": unique_id
                })
                response = json.dumps({"message": "Response from server", "sent_time": timer()})
                await websocket.send(response)
        except websockets.exceptions.ConnectionClosed:
            logging.info("Connection closed by client")
            self.connections.remove(websocket)

class WebSocketClient:
    def __init__(self, scenario_key, uri, parameter):
        settings = scenarios[scenario_key]
        self.metrics = metrics[scenario_key]
        self.uri = uri
        self.parameter = parameter
        self.interval = parameter if scenario_key == 'frequency' else settings['interval']
        self.payload_size = parameter if scenario_key == 'payload' else settings['payload_size']

    async def run(self):
        try:
            async with websockets.connect(self.uri) as ws:
                latencyList = []
                for _ in range(samplesPerParameter):
                    unique_id = str(uuid.uuid4())  # Generate a unique identifier for each message
                    sent_time = timer()
                    message = json.dumps({
                        "message": str(self.payload_size),
                        "sent_time": sent_time,
                        "id": unique_id
                    })
                    await ws.send(message)
                    response = await ws.recv()
                    data = json.loads(response)
                    latency = timer() - sent_time
                    latencyList.append(latency)

                    await asyncio.sleep(self.interval)

                average_latency = mean(latencyList)
                print(f"Average Latency: {average_latency}")
                self.metrics.log_message(self.parameter, "WebSocket", average_latency)

        except websockets.exceptions.ConnectionClosedError as e:
            print(f"WebSocket connection closed: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")


async def run_scenario(scenario_key, parameter, websocket_server):
    # Utilize the existing MQTT server and WebSocket server without reinitializing
    websocket_server.change_parameter(parameter)
    mqtt_client = MQTTClient(scenario_key, parameter)
    websocket_client = WebSocketClient(scenario_key, "ws://localhost:8765", parameter)

    mqtt_task = asyncio.create_task(mqtt_client.send_messages())
    websocket_client_task = asyncio.create_task(websocket_client.run())

    await asyncio.gather(mqtt_task, websocket_client_task)

async def main():
    global mqtt_server, websocket_server_task, websocket_server

    mqtt_server = MQTTServer()
    mqtt_server.start()

    websocket_server = WebSocketServer()
    websocket_server_task = websockets.serve(websocket_server.handle_connection, 'localhost', 8765)

    # Wait for the WebSocket server to start
    await websocket_server_task

    try:
        for scenario_key, settings in scenarios.items():
            websocket_server.change_metrics(scenario_key)
            parameters = linear_space(settings['start'], settings['end'], settings['num_values'])
            for parameter in parameters:
                logging.info(f"Running {scenario_key} scenario with parameter: {parameter}")
                await run_scenario(scenario_key, parameter, websocket_server)
    finally:
        print("final")
        metrics['frequency'].save_data()
        metrics['payload'].save_data()
        #metrics['concurrency'].save_data()
        # Stop the servers properly
        # mqtt_server.stop()
        # websocket_server_task.close()
        # await websocket_server_task.wait_closed()



if __name__ == "__main__":
    asyncio.run(main())