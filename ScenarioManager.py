# scenario_manager.py
class ScenarioManager:
    def __init__(self, scenarios):
        """
        Initialize the ScenarioManager with a dictionary of scenarios.

        :param scenarios: A dictionary where each key is a scenario name and the value is another dictionary
                          containing settings for that scenario.
        """
        self.scenarios = scenarios

    def get_scenario(self, scenario_key):
        """
        Retrieve the entire scenario configuration based on the scenario key.

        :param scenario_key: The key for the scenario to retrieve.
        :return: A dictionary containing the scenario configuration, or None if the scenario does not exist.
        """
        return self.scenarios.get(scenario_key)

    def get_setting(self, scenario_key, setting_name, default=None):
        """
        Retrieve a specific setting from a scenario configuration.

        :param scenario_key: The key for the scenario.
        :param setting_name: The name of the setting to retrieve.
        :param default: The default value to return if the setting or scenario_key does not exist.
        :return: The value of the setting if it exists, otherwise the default value.
        """
        scenario = self.scenarios.get(scenario_key, {})
        return scenario.get(setting_name, default)

    def update_scenario(self, scenario_key, new_settings):
        """
        Update or add new settings to a specific scenario.

        :param scenario_key: The key for the scenario to update.
        :param new_settings: A dictionary containing new or updated settings for the scenario.
        """
        if scenario_key not in self.scenarios:
            self.scenarios[scenario_key] = {}
        self.scenarios[scenario_key].update(new_settings)

    def list_scenarios(self):
        """
        List all available scenarios.

        :return: A list of scenario keys.
        """
        return list(self.scenarios.keys())
