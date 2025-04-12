import json


class Settings:
    def __init__(self, config_file='./app/appsettings.json'):
        with open(config_file) as f:
            self._config = json.load(f)

    def get(self, key, default=None):
        return self._config.get(key, default)