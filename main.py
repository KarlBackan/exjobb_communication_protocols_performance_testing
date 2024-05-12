from importsAndConfig import asyncio, websockets, scenarios, linear_space, logging
from ScenarioManager import ScenarioManager
from PerformanceMetrics import metrics
from MQTTClasses import MQTTClient, MQTTServer
from WebSocketClasses import WebSocketServer, WebSocketClient
# main.py
from ScenarioManager import ScenarioManager
from MQTTClasses import MQTTServer, MQTTClient
from WebSocketClasses import WebSocketServer, WebSocketClient
from importsAndConfig import scenarios, linear_space, logging, websockets

async def run_scenario(scenario_key, parameters, websocket_server, scenario_manager, use_websocket, use_mqtt):

    # Conditional execution of WebSocket operations based on user input
    if use_websocket:
        websocket_client = WebSocketClient(scenario_manager, scenario_key, "ws://localhost:8765", None)
        for parameter in parameters:
            logging.info(f"WebSocket: Running {scenario_key} scenario with parameter: {parameter}")
            websocket_server.scenario_key = scenario_key
            websocket_server.parameter = parameter
            websocket_client.parameter = parameter
            if scenario_key == "payload_metrics":
                websocket_client.payload_size = parameter  # Set payload size based on parameter
            await websocket_client.run()

    # Conditional execution of MQTT operations based on user input
    if use_mqtt:
        mqtt_client = MQTTClient(scenario_manager, scenario_key, None)
        mqtt_client.start()
        for parameter in parameters:
            logging.info(f"MQTT: Running {scenario_key} scenario with parameter: {parameter}")
            mqtt_client.parameter = parameter  # Assuming dynamic parameter update is possible
            if scenario_key == "payload_metrics":
                mqtt_client.payload_size = parameter
            await mqtt_client.send_messages()  # Ensure send_messages is correctly implemented in MQTTClient

async def main():
    # Initialization of scenario manager and server setups
    scenario_manager = ScenarioManager(scenarios)
    mqtt_server = MQTTServer()
    mqtt_server.start()
    websocket_server = WebSocketServer(scenario_manager)
    server_task = await websockets.serve(websocket_server.handle_connection, 'localhost', 8765)

    # User input for scenario selection and technology choices
    print("Available scenarios:")
    for key in scenarios:
        print(key)
    selected_scenario = input("Enter the scenario key you want to run, or 'all' to run all scenarios: ")
    use_websocket = input("Do you want to run WebSocket operations? (yes/no): ").lower() == 'yes'
    use_mqtt = input("Do you want to run MQTT operations? (yes/no): ").lower() == 'yes'

    scenarios_to_run = scenarios.keys() if selected_scenario == 'all' else [selected_scenario]

    try:
        for scenario_key in scenarios_to_run:
            if scenario_key in scenarios:
                settings = scenario_manager.scenarios[scenario_key]
                parameters = linear_space(settings['start'], settings['end'], settings['num_values'])
                logging.info(f"Starting {scenario_key} scenario with selected parameters.")
                await run_scenario(scenario_key, parameters, websocket_server, scenario_manager, use_websocket, use_mqtt)
            else:
                print(f"Scenario {scenario_key} not found.")
    finally:
        print("Final cleanup and data saving")
        for key, metric in metrics.items():
            try:
                metric.save_data()
                logging.info(f"Data for {key} saved successfully.")
            except Exception as e:
                logging.error(f"Failed to save data for {key}: {e}")


if __name__ == "__main__":
    asyncio.run(main())


