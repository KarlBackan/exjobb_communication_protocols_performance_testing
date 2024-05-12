# Assumed scenario configurations are placed in a separate module
from importsAndConfig import samplesPerParameter, interval_standard, scenarios, time, pd, warnings, logging, asyncio, os

import os
import asyncio
import pandas as pd
import psutil
from datetime import datetime
import logging

class PerformanceMetrics:
    def __init__(self, filename, scenario_description, process_id=None):
        self.filename = filename
        self.scenario_description = scenario_description
        self.process = psutil.Process(process_id) if process_id else psutil.Process()
        self.system_net_io = psutil.net_io_counters()
        self.data = pd.DataFrame(columns=[
            "Parameter", "Protocol", "Average CPU Usage (%)", "Total Memory Usage (Bytes)",
            "Total Disk Read (Bytes)", "Total Disk Write (Bytes)",
            "Network Bytes Sent", "Network Bytes Received",
            "Thread Count", "Resource Handles", "Duration (Seconds)"
        ])
        self.monitoring_task = None
        self.monitoring = False
        self.samples = []
        self.start_time = None  # To capture the start time of monitoring

    def start_monitoring(self):
        self.monitoring = True
        self.start_time = datetime.now()  # Start time is recorded when monitoring starts
        if not self.monitoring_task or self.monitoring_task.done():
            self.monitoring_task = asyncio.create_task(self.monitor())

    async def monitor(self):
        initial_net_io = self.system_net_io
        while self.monitoring:
            cpu = self.process.cpu_percent(interval=None)
            current_net_io = psutil.net_io_counters()
            resource_handles = self.process.num_handles() if hasattr(self.process, 'num_handles') else None
            snapshot = {
                'time': datetime.now(),
                'cpu': cpu,
                'memory': self.process.memory_info().rss,
                'disk_read': self.process.io_counters().read_bytes,
                'disk_write': self.process.io_counters().write_bytes,
                'net_sent': current_net_io.bytes_sent - initial_net_io.bytes_sent,
                'net_received': current_net_io.bytes_recv - initial_net_io.bytes_recv,
                'thread_count': self.process.num_threads(),
                'resource_handles': resource_handles
            }
            self.samples.append(snapshot)
            await asyncio.sleep(0.1)
            initial_net_io = current_net_io

    async def stop_monitoring(self):
        self.monitoring = False
        if self.monitoring_task:
            await self.monitoring_task

    async def calculate_and_save(self, parameter, protocol):
        end_time = datetime.now()  # Capture the end time of monitoring
        duration_seconds = (end_time - self.start_time).total_seconds() if self.start_time else 0
        df = pd.DataFrame(self.samples)
        summary = {
            "Parameter": parameter,
            "Protocol": protocol,
            "Average CPU Usage (%)": df['cpu'].mean(),
            "Total Memory Usage (Bytes)": df['memory'].mean(),
            "Total Disk Read (Bytes)": df['disk_read'].sum(),
            "Total Disk Write (Bytes)": df['disk_write'].sum(),
            "Network Bytes Sent": df['net_sent'].sum(),
            "Network Bytes Received": df['net_received'].sum(),
            "Thread Count": df['thread_count'].mean(),
            "Resource Handles": df['resource_handles'].mean() if 'resource_handles' in df.columns else None,
            "Duration (Seconds)": duration_seconds
        }
        self.data = pd.concat([self.data, pd.DataFrame([summary])], ignore_index=True)
        if not self.data.empty:
            self.data.to_csv(self.filename, mode='a', header=not os.path.exists(self.filename), index=False)
            logging.info(f"Performance data saved to {self.filename}.")
        self.data = pd.DataFrame(columns=self.data.columns)
        self.samples = []
        self.start_time = None  # Reset start time for the next monitoring session





# Initialize metrics instances for each scenario
metrics = {}
for key, settings in scenarios.items():
    print(settings)
    metrics[key] = PerformanceMetrics(f"{key}_performance.csv", settings['description'])