import configparser
import os
# # Constants
# CAR_LENGTH = 6
# FLOW_PER_LANE = 1800
# WAVE_COEFFICIENT = 18.5
#
# #Program settings.ini
# RESULT_PATH = "..\\results\\"
# SAVE_RESULTS = True
# SAVE_PLOTS = True
# SHOW_PLOTS = False
# GRAPH_TYPE = "graph"
# PLOT_TYPE = "plot"
# SHOW_TYPE = GRAPH_TYPE
#
# # changeable Program settings.ini
# STEPS = 24
# INTERVAL = 3600
# TIME_STEP = 1
# LOGGING_INTERVAL = INTERVAL
#
# # generator settings.ini
# GRID_SIZE = 4
#
#
#
# YAML_OPTION_PERIOD = "Zeitschritt"
# YAML_OPTION_INTERVAL = "Zeitintervall"
# YAML_OPTION_DURATION = "Simulationsschritt"
# YAML_OPTION_LOGGING_INTERVAL = "Loggingintervall"
# YAML_SEGMENT = "Segmente"
# YAML_OPTION = "Optionen"

SETTINGS_FILE = "settings.ini"
settings = None
class _Settings:

    def __init__(self, settings_file=SETTINGS_FILE):
        self.SETTINGS_FILE = settings_file

        # standard values

        # Simulation constants
        self.CAR_LENGTH = 6
        self.FLOW_PER_LANE = 1800
        self.WAVE_COEFFICIENT = 18.5

        #Program settings.ini
        self.RESULT_PATH = "..\\results\\"
        self.SAVE_RESULTS = True
        self.SAVE_PLOTS = True
        self.SHOW_PLOTS = False
        self.GRAPH_TYPE = "graph"
        self.PLOT_TYPE = "plot"
        self.SHOW_TYPE = self.GRAPH_TYPE

        # changeable Program settings.ini
        self.STEPS = 24
        self.INTERVAL = 3600
        self.TIME_STEP = 1
        self.LOGGING_INTERVAL = self.INTERVAL

        # generator settings.ini
        self.GRID_SIZE = 4

        self.YAML_OPTION_PERIOD = "Zeitschritt"
        self.YAML_OPTION_INTERVAL = "Zeitintervall"
        self.YAML_OPTION_DURATION = "Simulationsschritt"
        self.YAML_OPTION_LOGGING_INTERVAL = "Loggingintervall"
        self.YAML_SEGMENT = "Segmente"
        self.YAML_OPTION = "Optionen"

        self.__import_settings__()


    def __determine_settings_path__(self):
        if os.path.exists(self.SETTINGS_FILE):
            return self.SETTINGS_FILE
        else:
            return "..\\resources\\" + self.SETTINGS_FILE

    def __import_settings__(self):
        # import all settings.ini from the settings.ini file
        config = configparser.ConfigParser()

        if not config.read(self.__determine_settings_path__()):
            print("Could not read settings.ini file")
            return
        if config.has_section("generator_settings"):
            self.STEPS = int(config["generator_settings"]["STEPS"])
            self.INTERVAL = int(config["generator_settings"]["INTERVAL"])
            self.TIME_STEP = int(config["generator_settings"]["TIME_STEP"])
            self.LOGGING_INTERVAL = int(config["generator_settings"]["LOGGING_INTERVAL"])
        if config.has_section("program_settings"):
            self.RESULT_PATH = config["program_settings"]["RESULT_PATH"]
            self.SAVE_RESULTS = config["program_settings"]["SAVE_RESULTS"] == "True"
            self.SAVE_PLOTS = config["program_settings"]["SAVE_PLOTS"] == "True"
            self.SHOW_PLOTS = config["program_settings"]["SHOW_PLOTS"] == "True"
            self.SHOW_TYPE = config["program_settings"]["SHOW_TYPE"]
        if config.has_section("sim_constants"):
            self.CAR_LENGTH = int(config["sim_constants"]["CAR_LENGTH"])
            self.FLOW_PER_LANE = int(config["sim_constants"]["FLOW_PER_LANE"])
            self.WAVE_COEFFICIENT = float(config["sim_constants"]["WAVE_COEFFICIENT"])
        if config.has_section("key_constants"):
            self.YAML_OPTION_INTERVAL = config["key_constants"]["YAML_OPTION_INTERVAL"]
            self.YAML_OPTION_DURATION = config["key_constants"]["YAML_OPTION_DURATION"]
            self.YAML_OPTION_PERIOD = config["key_constants"]["YAML_OPTION_PERIOD"]
            self.YAML_OPTION_LOGGING_INTERVAL = config["key_constants"]["YAML_OPTION_LOGGING_INTERVAL"]
            self.YAML_SEGMENT = config["key_constants"]["YAML_SEGMENT"]
            self.YAML_OPTION = config["key_constants"]["YAML_OPTION"]
    def set_settings(self, dict : dict):
        for key, value in dict.items():
            setattr(self, key, value)



def get_settings():
    global settings
    if not settings:
        settings = _Settings()
    return settings

#The following files were used for the benchmark. To use this variable change the call of the file in the simulation file.
#SIM_FILE = "..\\networks\\medium.yml"
#SIM_FILE = "..\\networks\\small.yml"
#SIM_FILE = "..\\networks\\huge.yml"
