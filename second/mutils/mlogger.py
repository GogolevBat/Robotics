import datetime
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QTextEdit
class Logger:
    def __init__(self, field: QTextEdit):
        self.log_field = field

        self.logs = {}
        self.index = 0
    def _set(self, message, level="INFO"):
        dt = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M:%S.%f")
        log = f"[{dt}][{level}] - {message}"
        print(log)
        self.log_field.insertHtml(f"<span>{log}</span>")
        self.log_field.insertPlainText("\n")

        self.log_field.moveCursor(QTextCursor.End)

        self.logs[self.index] = [dt, level, message]
        self.index += 1
        if (c:=(self.index-1000)) in self.logs:
            del self.logs[c]

    def info(self, *args):
        message = " ".join(map(str, args))
        self._set(message, "INFO")
    def debug(self, *args):
        message = " ".join(map(str, args))
        self._set(message, "DEBUG")
    def error(self, *args):
        message = " ".join(map(str, args))
        self._set(message, "ERROR")
    def warning(self, *args):
        message = " ".join(map(str, args))
        self._set(message, "WARNING")
