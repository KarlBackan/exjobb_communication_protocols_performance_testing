import asyncio
import json
import logging
import os
import random
import time
import uuid
from datetime import datetime
from statistics import mean
from time import perf_counter
from timeit import default_timer as timer
import pandas as pd
import paho.mqtt.client as mqtt
import websockets
import warnings
samplesPerParameter = 10000
interval_standard = 0
payload_standard = 1024
from ScenarioManager import ScenarioManager

# Setup detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
def linear_space(start, end, num):
    step = (end - start) / (num - 1)
    return [start + step * i for i in range(num)]

# Define scenarios
# Define scenarios with consistent keys for range values
scenarios = {
    "payload_metrics": {"start": 1000, "end": 10000, "num_values": 10, "interval": 1, "description": "Varying payload sizes."},
}

# Utility functions
def generate_payload(size):
    return json.dumps({"message": "X" * int(float(size)), "sent_time": datetime.now().isoformat(), "id": str(uuid.uuid4())})


# Initialize the Scenario Manager
scenario_manager = ScenarioManager(scenarios)

# Example usage
frequency_settings = scenario_manager.get_scenario("frequency")
print("Frequency Scenario:", frequency_settings)

payload_interval = scenario_manager.get_setting("payload", "interval")
print("Payload Interval:", payload_interval)

# Update a scenario setting
scenario_manager.update_scenario("payload_metrics", {"payload_size": 5000})
updated_payload_size = scenario_manager.get_setting("payload", "payload_size")
print("Updated Payload Size:", updated_payload_size)