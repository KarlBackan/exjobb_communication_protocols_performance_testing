from PerformanceMetrics import metrics
from importsAndConfig import samplesPerParameter, interval_standard, payload_standard, scenarios, logging, asyncio, websockets, json, timer, uuid, mean

from websockets import connect

class WebSocketServer:
    def __init__(self, scenario_manager):
        self.scenario_manager = scenario_manager
        self.parameter = None
        self.connections = set()

    def change_parameter(self, scenario_key, parameter_name):
        self.parameter = self.scenario_manager.get_setting(scenario_key, parameter_name)

    async def handle_connection(self, websocket, path):
        self.connections.add(websocket)
        try:
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                unique_id = str(uuid.uuid4())
                response = json.dumps({
                    "message": "X" * int(float(data["message"])),
                    "sent_time": timer(),
                    "id": unique_id
                })
                await websocket.send(response)
        except websockets.exceptions.ConnectionClosed:
            logging.info("Connection closed by client")
            self.connections.remove(websocket)

class WebSocketClient:
    def __init__(self, scenario_manager, scenario_key, uri, parameter):
        self.scenario_manager = scenario_manager
        self.uri = uri
        self.scenario_key = scenario_key
        self.setup_scenario()
        self.parameter = parameter

    def setup_scenario(self):
        self.interval = self.scenario_manager.get_setting(self.scenario_key, 'interval', interval_standard)
        self.payload_size = self.scenario_manager.get_setting(self.scenario_key, 'payload_size', payload_standard)

    async def run(self):
        latency_list = []
        try:
            async with connect(self.uri) as ws:
                for _ in range(samplesPerParameter):
                    unique_id = str(uuid.uuid4())
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
                    latency_list.append(latency)

                    await asyncio.sleep(self.interval)

                average_latency = mean(latency_list)
                metrics[self.scenario_key].log_message(self.parameter, "WebSocket", average_latency)
                logging.info(f"Recorded Average Latency for Websocket: {average_latency}s")
        except websockets.exceptions.WebSocketException as e:
            print(f"WebSocket error: {e}")
