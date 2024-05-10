# Assumed scenario configurations are placed in a separate module
from importsAndConfig import samplesPerParameter, scenarios, time, pd, warnings, logging, asyncio, os
class PerformanceMetrics:
    def __init__(self, filename, scenario_description):
        self.start_time = time.time()
        self.filename = filename
        self.scenario_description = scenario_description
        self.data = pd.DataFrame(columns=[
            "Parameter", "Average Latency", "Samples", "Protocol"
        ])
        self.log_counter = 0
        logging.info(f"Starting test scenario: {scenario_description}")

    def log_message(self, parameter, protocol, latency):
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        new_data = pd.DataFrame([{
            "Parameter": parameter,
            "Average Latency": latency,
            "Samples": samplesPerParameter,
            "Protocol": protocol,
        }])

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FutureWarning)
            self.data = pd.concat([self.data, new_data], ignore_index=True)

    def save_data(self):
        if not self.data.empty:
            self.data.to_csv(self.filename, mode='a', header=not os.path.exists(self.filename), index=False)
            logging.info(f"Performance data saved to {self.filename}. Data reset.")
            self.data = pd.DataFrame(columns=self.data.columns)  # Reset the DataFrame

    async def log_performance(self):
        # This function might not be needed if you call save_data() explicitly after test runs
        while True:
            await asyncio.sleep(60)  # Example: Save every 60 seconds if needed
            self.save_data()


# Initialize metrics instances for each scenario
metrics = {}
for key, settings in scenarios.items():
    print(settings)
    metrics[key] = PerformanceMetrics(f"{key}_performance.csv", settings['description'])