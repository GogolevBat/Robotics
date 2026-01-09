from asyncio import create_task
from datetime import datetime

from PyQt5.QtWidgets import QTextEdit


class LogEmitter:
    def __init__(self, window: "MainWindow"):
        self._window = window


    async def log(self, level, text, bkcolor="white", tcolor="black"):
        print(f"{datetime.now().strftime("%Y/%d/%m %H:%M:%S")} - {level} - {text}")
        log_message = f"{datetime.now().strftime("%Y/%d/%m %H:%M:%S")} - <span style='background-color:{bkcolor}; color: {tcolor};'>{level} - {text}</span>"
        self._window.ui.logs_field: QTextEdit
        self._window.ui.logs_field.insertHtml(log_message)
        self._window.ui.logs_field.insertPlainText("\n")
        if self._window.ui.flag_logs_to_csv.isChecked():
            self._window.logs_queue.put_nowait(log_message)

    def info(self, text):
        create_task(self.log("INFO",text, bkcolor="white"))
    def debug(self, text):
        create_task(self.log("DEBUG", text, bkcolor="blue"))
    def warning(self, text):
        create_task(self.log("WARNING",text,bkcolor="yellow"))
    def error(self, text):
        create_task(self.log("ERROR", text, bkcolor="red", tcolor="white"))