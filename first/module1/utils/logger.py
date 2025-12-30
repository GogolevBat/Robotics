from asyncio import create_task
from datetime import datetime

class LogEmitter:
    def __init__(self, window: "MainWindow"):
        self._window = window

    async def log(self, level, text):
        log_message = f"\n{datetime.now().isoformat()[:-4]} - {level} - {text}"
        print(log_message)
        self._window.ui.logs_field.insertPlainText(log_message)
        if self._window.ui.flag_logs_to_csv.isChecked():
            self._window.logs_queue.put_nowait(log_message)

    def info(self, text):
        create_task(self.log("INFO",text))
    def debug(self, text):
        create_task(self.log("DEBUG",text))
    def warning(self, text):
        create_task(self.log("WARNING",text))
    def error(self, text):
        create_task(self.log("ERROR",text))