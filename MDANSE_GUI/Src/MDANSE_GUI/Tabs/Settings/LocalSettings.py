class LocalSettings:
    def __init__(self, *args, **kwargs):
        self._settings = {}

    def get(self, key: str):
        temp = self._settings.get(key, None)
        return temp

    def set(self, key: str, value: str):
        self._settings[key] = value
