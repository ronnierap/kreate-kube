import logging

logger = logging.getLogger(__name__)

class Trace:
    def __init__(self) -> None:
        self.stack = []

    def push(self, msg:str):
        logger.debug(msg)
        self.stack.append(msg)

    def push_info(self, msg:str):
        logger.info(msg)
        self.stack.append(msg)

    def pop(self):
        logger.debug("popping: " + self.stack.pop())

    def print_last(self):
        print(f"while: {self.stack[-1]}")

    def print_all(self):
        for line in self.stack:
            print(f"while: {line}")
