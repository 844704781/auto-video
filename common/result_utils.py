from typing import Optional


class ResultDo:
    def __init__(self, code: int, message: str = None, data: object = None):
        self._code = code
        self._message = message
        self._data = data

    @property
    def code(self):
        return self._code

    @property
    def message(self):
        return self._message

    @property
    def data(self):
        return self._data
