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
interval_standard = 0.1
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
    "frequency_metrics": {"start": 0.01, "end": 1, "num_values": 10, "payload_size": 50, "description": "Varying message frequency."},
    "payload_metrics": {"start": 100, "end": 1000000, "num_values": 10, "interval": 5, "description": "Varying payload sizes."},
    #"concurrency": {"start": 1, "end": 10, "num_values": 10, "interval": 3, "description": "Varying number of clients."}
}

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