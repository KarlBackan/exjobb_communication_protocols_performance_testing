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
        self.parameter = parameter

    async def send_and_receive(self, ws):
        # Create a message
        message = json.dumps({
            "message": str(self.parameter),
            "sent_time": datetime.now().isoformat(),
            "id": str(uuid.uuid4())
        })
        # Send the message
        await ws.send(message)
        # Wait for the response immediately after sending
        response = await ws.recv()
        return response

    async def run(self):
        metrics[self.scenario_key].start_monitoring()
        responses = []
        try:
            # Connect to the WebSocket server
            async with connect(self.uri) as ws:
                # Create a list of tasks where each task involves sending a message and waiting for its response
                tasks = [self.send_and_receive(ws) for _ in range(samplesPerParameter)]
                # Execute all tasks concurrently and wait for all to complete
                responses = await asyncio.gather(*tasks)
        except Exception as e:
            logging.error(f"Error during WebSocket communication: {str(e)}")
        finally:
            # Stop monitoring and process performance data
            await metrics[self.scenario_key].stop_monitoring()
            await metrics[self.scenario_key].calculate_and_save(self.parameter, 'WebSocket')
            await asyncio.sleep(interval_standard)
            return responses