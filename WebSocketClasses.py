from datetime import datetime

from PerformanceMetrics import metrics
from importsAndConfig import samplesPerParameter, interval_standard, payload_standard, scenarios, logging, asyncio, websockets, json, timer, uuid, mean

from websockets import connect

class WebSocketServer:
    def __init__(self, scenario_manager):
        self.scenario_manager = scenario_manager
        self.scenario_key = ""
        self.parameter = ""
        self.connections = set()
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
        finally:
            self.connections.remove(websocket)


class WebSocketClient:
    def __init__(self, scenario_manager, scenario_key, uri, parameter):
        self.scenario_manager = scenario_manager
        self.uri = uri
        self.scenario_key = scenario_key
        self.parameter = parameter  # Make sure this is used correctly
        self.payload_size = parameter  # Initialize with the passed parameter, adjust later if needed

    async def run(self):
        metrics[self.scenario_key].start_monitoring()
        try:
            async with connect(self.uri) as ws:
                for _ in range(samplesPerParameter):
                    message = json.dumps({
                        "message": str(self.payload_size),  # Ensure payload_size is updated if parameter changes
                        "sent_time": datetime.now().isoformat(),
                        "id": str(uuid.uuid4())
                    })
                    await ws.send(message)
                    await ws.recv()  # Assume response handling here
        finally:
            await metrics[self.scenario_key].stop_monitoring()
            await metrics[self.scenario_key].calculate_and_save(self.parameter, 'WebSocket')
            await asyncio.sleep(interval_standard)
