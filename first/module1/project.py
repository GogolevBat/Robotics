import asyncio
import datetime
import random
import sys
from asyncio import create_task
from functools import wraps
from typing import Any, Callable, Literal
import aiohttp
from PyQt5.QtCore import QSize
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QMainWindow, QWidget, QTableWidget, QTableWidgetItem, QLabel, QStyle, QHBoxLayout, \
    QPushButton, QTextEdit, QLayout, QVBoxLayout, QSlider
from PyQt6.QtCore import QTimer
from qasync import QEventLoop, QApplication, asyncSlot

from first.module1.utils.hand_move import Moving
from motion.core import RobotControl, LedLamp
from designe import Ui_Dialog
import aiofiles
import aiofiles.os as aos
import aiocsv
from utils.logger import LogEmitter
from utils.lamp import MyLamp
from utils.nepovtorimiy_original import MotionBlurRobot

class TIPOROBOT:
    def __init__(self, robot: RobotControl):
        ...
    def __getattr__(self, arg):
        def wrapper(*args, **kwargs):
            # print(f"(RobotControl) метод: {arg}({args, kwargs})")
            return [random.randint(1,157)/100 for _ in range(6)]
        return wrapper



robot = MotionBlurRobot() # Так как я не знаю что возвращает api то дальше код с api будет примерный!
# В документации не было примеров возврата, либо я не нашел

def update_table(table: QTableWidget, columns: list, matrix: list[list[Any]], indexes:list=None) -> QTableWidget:
    table.setRowCount(len(matrix))
    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(columns)
    if indexes:
        table.setVerticalHeaderLabels(indexes)
    for i, row in enumerate(matrix):
        for j, col in enumerate(row):
            table.setItem(i, j, QTableWidgetItem(f"{col}"))
    return table

class MainWindow(QMainWindow, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.ui_init()
        self.logs_queue = asyncio.Queue()
        self.logger = LogEmitter(self)

    def ui_init(self):
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.lamp = MyLamp(self.ui)

        # Добавляем к каждой кнопке движения, ассинхронный слот на конкретное управление
        for mt in self.ui.__dict__: # Подключение ручного управления
            if isinstance(self.ui.__dict__[mt], QSlider) and "MoveJ" in mt:

                slider: QSlider = self.ui.__dict__[mt]
                method_ = Moving(
                    slider=slider,
                    joint=int(mt[-1]),
                    astype=-1 if mt[-1] == "m" else 1,
                    pwindow=self,
                    robot=robot
                )
                slider.valueChanged.connect(method_)
                slider.sliderReleased.connect(method_.hand_stop)

            if isinstance(self.ui.__dict__[mt], QSlider) and "MoveL" in mt:

                slider: QSlider = self.ui.__dict__[mt]
                method_ = Moving(
                    slider=slider,
                    joint=int(mt[-1]),
                    astype=-1 if mt[-1] == "m" else 1,
                    pwindow=self,
                    robot=robot,
                    move="l"
                )
                print(slider)
                slider.valueChanged.connect(method_)
                slider.sliderReleased.connect(method_.hand_stop)


        self.ui.STOP_I_TOCHKA.clicked.connect(self.stop_)
        self.ui.robot_power_on.clicked.connect(self._start_motion)
        self.ui.robot_power_off.clicked.connect(self.stop_)

        self.ui.flag_logs_to_csv.clicked.connect(self.log_logs_to_csv)

        self.ui.logs_field.textChanged.connect(self.log_change_text)

        self.ui.take_and_put.clicked.connect(self._take_put_motion)



    def log_change_text(self):
        self.ui.logs_field.moveCursor(QTextCursor.End)

    def _take_put_motion(self):
        if self.ui.take_and_put.isChecked():
            robot.toolON()
            self.logger.info("Захват объекта")
        else:
            robot.toolOFF()
            self.logger.info("Отхват объекта")

    def _start_motion(self):
        self.logger.info("Запуск моторов робота")
        robot.engage()
        robot.moveToInitialPose()

    def stop_(self):
        self.logger.info("Остановка робота")
        robot.disengage()

    def log_logs_to_csv(self):
        if self.ui.flag_logs_to_csv.isChecked():
            self.logs_file = f"logs/{datetime.datetime.now().strftime("%Y%m%d-%H%M%S.csv")}"
            self.new_file = True


    async def update_table_axes_joints(self):
        tasks = [
            asyncio.to_thread(robot.getMotorPositionRadians),
            asyncio.to_thread(robot.getMotorPositionTick),
            asyncio.to_thread(robot.getActualTemperature),
            asyncio.to_thread(robot.get_motor_degree_position),
        ]
        data = await asyncio.gather(*tasks)
        update_table(
            self.ui.table_axes_joints,
            ["J1", "J2", "J3", "J4", "J5", "J6"],
            data,
            indexes=["radians", "ticks", "temperature", "degrees"],
        )
    async def update_table_position_robot(self):
        data = [
            await asyncio.to_thread(robot.getLinearTrackPosition)
        ]
        update_table(
            self.ui.table_position_robot,
            ["x", "y", "z"],
            data
        )
    async def lifespan(self):
        tasks = [
            self.update_table_axes_joints(),
            self.update_table_position_robot()
        ]
        await asyncio.gather(*tasks)

    async def logs_manager(self):
        sep = ";"
        chunk_size = 5 # Вероятно из-за этого не все логи будут сохраняться и вынести в .env но не сегодня
        logs = []
        while True:
            await asyncio.sleep(0.1)
            log = await self.logs_queue.get()
            logs.append(log)
            if len(logs) < chunk_size:
                continue
            print("logs_manager Обработка лога в файл")
            async with aiofiles.open(self.logs_file, mode="a") as f: # Можно было использовать aiocsv
                if self.new_file:
                    self.new_file = False
                    await f.write(sep.join(["Дата", "Тип", "Содержание"]))
                await f.write(sep.join(log.split(" - ")))

async def main(stop_event: asyncio.Event, window: MainWindow):
    asyncio.create_task(window.logs_manager())
    while not stop_event.is_set():
        await asyncio.sleep(3)
        await window.lifespan()

if __name__ == '__main__':

    app = QApplication(sys.argv)

    stop_event = asyncio.Event()
    app.aboutToQuit.connect(stop_event.set)
    window = MainWindow()

    window.show()

    asyncio.run(main(stop_event, window), loop_factory=QEventLoop)
