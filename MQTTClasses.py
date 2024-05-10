# Assumed scenario configurations are placed in a separate module
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

class MQTTClient:
    def __init__(self, scenario_manager, scenario_key, parameter):
        self.scenario_manager = scenario_manager
        self.parameter = parameter
        self.scenario_key = scenario_key
        settings = scenario_manager.get_scenario(scenario_key)
        self.interval = settings.get('interval', interval_standard)
        self.payload_size = settings.get('payload_size', payload_standard)
        self.latency_list = []

        client_id = f'python-mqtt-{random.randint(0, 1000)}'
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f'python-mqtt-{random.randint(0, 1000)}', protocol=mqtt.MQTTv5)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect("localhost", 1883, 60)

    def on_connect(self, client, userdata, flags, rc, properties=None):
        client.subscribe("test/response")

    def on_message(self, client, userdata, msg):
        data = json.loads(msg.payload.decode())
        latency = timer() - data['sent_time']
        self.latency_list.append(latency)

    async def send_messages(self):
        self.client.loop_start()
        for _ in range(samplesPerParameter):
            unique_id = str(uuid.uuid4())
            message = json.dumps({"message": str(self.payload_size), "sent_time": timer(), "id": unique_id})
            self.client.publish("test/topic", message)
            await asyncio.sleep(self.interval)
        average_latency = mean(self.latency_list) if self.latency_list else None
        if average_latency:
            metrics[self.scenario_key].log_message(self.parameter, "MQTT", average_latency)
            logging.info(f"Recorded Average Latency for MQTT: {average_latency}s")

