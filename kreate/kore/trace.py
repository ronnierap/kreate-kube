import logging

logger = logging.getLogger(__name__)

# Add a trace logging level
# See: https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility
# TRACE = 9
# logging.addLevelName(TRACE, "TRACE")
# def trace(self, message, *args, **kws):
#    self._log(TRACE, message, args, **kws)
# logging.Logger.trace = trace


class Trace:
    def __init__(self) -> None:
        self.stack = []

    def push(self, msg: str):
        logger.log(5, msg)
        self.stack.append(msg)

    def push_info(self, msg: str):
        logger.info(msg)
        self.stack.append(msg)

    def pop(self):
        logger.log(5, "popping: " + self.stack.pop())

    def print_last(self):
        if len(self.stack) > 0:
            print(f"while: {self.stack[-1]}")

    def print_all(self):
        for line in self.stack:
            print(f"while: {line}")
