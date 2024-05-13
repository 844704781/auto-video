class CustomException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return '{code:%d,message:%s}' % (self.code, self.message)
