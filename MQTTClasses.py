# Assumed scenario configurations are placed in a separate module
from datetime import datetime

from PerformanceMetrics import metrics
from importsAndConfig import samplesPerParameter, interval_standard, payload_standard, scenarios, logging, asyncio, random, mqtt, json, timer, uuid, mean

# MQTTClasses.py
import json
import logging
import random
import uuid
import paho.mqtt.client as mqtt
from importsAndConfig import timer, scenarios
class MQTTServer:
    def __init__(self):
        client_id = f'python-mqtt-{random.randint(0, 1000)}'
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
        message = json.dumps({"message": "X" * int(float(data["message"])), "sent_time": sent_time, "id": unique_id})
        client.publish("test/response", message)

    def start(self):
        self.client.connect("localhost", 1883, 60)
        self.client.loop_start()
        logging.info("MQTT Server started and listening")


import json
import asyncio
import paho.mqtt.client as mqtt
from datetime import datetime
from PerformanceMetrics import metrics


class MQTTClient:
    def __init__(self, scenario_manager, scenario_key, parameter):
        self.scenario_manager = scenario_manager
        self.scenario_key = scenario_key
        self.parameter = parameter
        self.settings = scenario_manager.get_scenario(scenario_key)
        self.interval = self.settings.get('interval', interval_standard)

        self.payload_size = payload_standard
        self.response_count = 0
        self.expected_responses = samplesPerParameter

        client_id = f'python-mqtt-{random.randint(0, 1000)}'
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, protocol=mqtt.MQTTv5)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # Using an asyncio.Event to control the flow based on message reception
        self.all_responses_received = asyncio.Event()

    def on_connect(self, client, userdata, flags, rc, properties=None):
        print(f"Connected with result code {rc}")
        client.subscribe("test/response")

    def on_message(self, client, userdata, msg):
        data = json.loads(msg.payload.decode())
        # Increment response count upon each message reception
        self.response_count += 1

        if self.response_count >= self.expected_responses:
            self.response_count = 0
            self.all_responses_received.set()  # Signal that all messages have been received

    async def send_messages(self):
        async def send_message_loop():
            for num in range(samplesPerParameter):
                message = json.dumps({
                    "message": str(self.payload_size),
                    "scenario_key": self.scenario_key,
                    "sent_time": datetime.now().isoformat(),
                    "id": str(uuid.uuid4())
                })
                self.client.publish("test/topic", message)  # Ensure this is awaited if it's async
                await asyncio.sleep(0)

        metrics[self.scenario_key].start_monitoring()
        send_task = asyncio.create_task(send_message_loop())  # Create a task for sending messages
        await self.all_responses_received.wait()  # Wait for all responses before proceeding
        await send_task  # Optionally wait for the sending task to complete if needed
        await metrics[self.scenario_key].stop_monitoring()
        await metrics[self.scenario_key].calculate_and_save(self.parameter, "MQTT")
        await asyncio.sleep(interval_standard)

    def start(self):
        self.client.connect("localhost", 1883, 60)
        self.client.loop_start()
        logging.info("MQTT Server started and listening")