import asyncio
from typing import Literal

from PyQt5.QtWidgets import QLabel
from .nepovtorimiy_original import LedLamp
from dataclasses import dataclass

if __name__ == '__main__':
    from first.module1.designe import Ui_Dialog
@dataclass
class LampValue:
    widget: QLabel
    style: str

class MyLamp(LedLamp):
    def __init__(self, ui_dialog, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setLamp("0000")

        self.ui_dialog:"Ui_Dialog" = ui_dialog

        self.all_types: dict[str, LampValue] = {
            "stop": LampValue(widget=self.ui_dialog.lamp_stoped, style="background-color: red;"),
            "pause": LampValue(widget=self.ui_dialog.lamp_paused, style="background-color: yellow;"),
            "wait": LampValue(widget=self.ui_dialog.lamp_waiting, style="background-color: blue;"),
            "work": LampValue(widget=self.ui_dialog.lamp_working, style="background-color: green;")
        }

    def _set(self, key: Literal["stop", "pause", "wait", "work", "clear"] = "clear"):
        for lmp in self.all_types.values():
            lmp.widget.setStyleSheet("background-color: red;")

        if key in self.all_types:
            lmp = self.all_types[key]
            lmp.widget.setStyleSheet(lmp.style)


    async def stoped(self):
        self._set("stop")
        return await asyncio.to_thread(self.setLamp, "0001")

    async def working(self):
        self._set("work")
        return await asyncio.to_thread(self.setLamp, "0100")

    async def paused(self):
        self._set("pause")
        return await asyncio.to_thread(self.setLamp, "0010")

    async def waiting(self):
        self._set("wait")
        return await asyncio.to_thread(self.setLamp, "1000")

    async def clear(self):
        self._set("clear")
        return await asyncio.to_thread(self.setLamp, "0000")

    def madnes(self):
        """
        Вы знаете что такое безумие?
        :return:
        """
        self._set("clear")
        asyncio.create_task(asyncio.to_thread(self.setLamp, "1111"))
