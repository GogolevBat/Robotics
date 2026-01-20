from PyQt5.QtWidgets import QLabel

class Lamp:
    def __init__(self, lamp_field: QLabel):
        self.lamp_field = lamp_field
    def _set(self, color="#ffffff"):
        self.lamp_field.setStyleSheet(f"background-color: {color};")
    def red(self):
        self._set("#ff0000")
    def blue(self):
        self._set("#0000ff")
    def yellow(self):
        self._set("#ffff00")
    def green(self):
        self._set("#00ff00")