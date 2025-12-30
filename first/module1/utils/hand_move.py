import asyncio
from typing import Literal

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QPushButton, QSlider
from qasync import asyncSlot


class Moving(QObject):
    """
    Класс для быстрого присваниваний функций движения кнопкам
    """
    def __init__(self, slider:QSlider, joint:int, astype:int, pwindow: "MainWindow", robot, move: Literal["j", "l"] = "j"):
        super().__init__()
        self.slider = slider
        self.astype = astype
        self.joint = joint
        self.window = pwindow
        self.method = self.movej if move == "j" else self.movel
        self.robot = robot

    async def movel(self):
        # logger.info(f"Гартезианское управление joint={self.joint}, astype={self.astype}")
        if not self.window.ui.hand_mode.isChecked():
            self.window.logger.error("Не включено ручное управление!")
            return
        await asyncio.to_thread(self.robot.manualCartMode)
        position = self.slider.sliderPosition() - 1
        movement = [.0, .0, .0, .0, .0, .0]
        velocity = 0.05 * position
        movement[self.joint - 1] = velocity
        self.window.logger.info(f"Движение бесконечности {movement}")

    async def movej(self):
        if not self.window.ui.hand_mode.isChecked():
            self.window.logger.error(f"Не включено ручное управление!")
            return
        await asyncio.to_thread(self.robot.manualJointMode)
        position = self.slider.sliderPosition() - 1

        movement = [.0, .0, .0, .0, .0, .0]
        velocity = 0.05 * position
        movement[self.joint - 1] = velocity
        self.window.logger.info(f"Движение бесконечности {movement}")

    @asyncSlot()
    async def hand_stop(self):
        self.window.logger.info(f"Остановка движения")
        self.slider.setSliderPosition(1)

    @asyncSlot()
    async def __call__(self):
        return await self.method()