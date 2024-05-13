from importsAndConfig import samplesPerParameter, generate_payload, interval_standard, scenarios, logging, asyncio, timer
from PerformanceMetrics import metrics
import paramiko
import json
import os
class SFTPServer:
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def start_server(self):
        print("SFTP Server is ready to accept connections.")

    def handle_file(self, file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
            print(f"Received payload: {data}")

class SFTPClient:
    def __init__(self, host, port, username, password, scenario_manager, scenario_key, parameter):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.scenario_manager = scenario_manager
        self.scenario_key = scenario_key
        self.parameter = parameter
        self.transport = None
        self.sftp = None
        self.file_path = os.path.join(os.getcwd(), "reusable_payload.json")  # Reusable file

    async def connect(self):
        self.transport = paramiko.Transport((self.host, self.port))
        self.transport.connect(username=self.username, password=self.password)
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        logging.info("Connected to SFTP server")

    async def prepare_file(self):
        payload = generate_payload(self.parameter)
        with open(self.file_path, 'w') as file:
            file.write(payload)
        logging.info(f"File prepared for upload: {self.file_path}")

    async def send_file(self):
        await self.prepare_file()
        metrics[self.scenario_key].start_monitoring()
        remote_directory = 'C:/ProgramData/'  # Assuming '/upload/' is a valid directory on your SFTP server
        for _ in range(samplesPerParameter):
            try:
                remote_path = os.path.join(remote_directory, os.path.basename(self.file_path))
                await asyncio.to_thread(self.sftp.put, self.file_path, remote_path)
            except Exception as e:
                logging.error(f"Failed to upload file to {remote_path}: {str(e)}")
        os.remove(self.file_path)  # Cleanup the single file after all uploads
        logging.info("Temporary file removed after upload attempts")
        await metrics[self.scenario_key].stop_monitoring()
        await metrics[self.scenario_key].calculate_and_save(self.parameter, "SFTP")

    async def close(self):
        if self.sftp:
            self.sftp.close()
        if self.transport:
            self.transport.close()
        logging.info("SFTP connection closed")
