from resources import Settings
import yaml
import logging
class NetworkYAMLImport:
    def __init__(self, file_path):
        self.file_path = file_path
        self.settings = Settings.get_settings()
        self.options = None
        self.segments = None

    def import_file(self):
        self.__load_yaml__()
        self.__set_settings__()
        return self.segments

    def __load_yaml__(self):
        try:
            with open(self.file_path, "r") as file:
                yaml_input = yaml.safe_load(file)
        except FileNotFoundError:
            logging.error(f"File {self.file_path} not found.")
            return

        self.__set_segments__(yaml_input)
        self.__set_options__(yaml_input)


    def __set_segments__(self, yaml_input):
        try:
            if segments := yaml_input[self.settings.YAML_SEGMENT]:
                self.segments = segments
            else:
                raise KeyError
        except KeyError:
            logging.error(f"No segments given in {self.file_path}.")
            return

    def __set_options__(self, yaml_input):
        try:
            if options := yaml_input[self.settings.YAML_OPTION]:
                self.options = options
            else:
                raise KeyError
        except KeyError:
            logging.error(f"No options given in {self.file_path}.")
            return
    def __set_settings__(self):
        settings_dict = {"INTERVAL": self.options[self.settings.YAML_OPTION_INTERVAL],
                            "STEPS": self.options[self.settings.YAML_OPTION_DURATION],
                            "TIME_STEP": self.options[self.settings.YAML_OPTION_PERIOD],
                            "LOGGING_INTERVAL": self.options[self.settings.YAML_OPTION_LOGGING_INTERVAL]}
        self.settings.set_settings(settings_dict)
    def get_segments(self):
        return self.segments

    def __get_options__(self):
        return self.options

