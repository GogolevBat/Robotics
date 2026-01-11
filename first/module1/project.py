import asyncio
import datetime
import random
import sys
import time
from asyncio import create_task
from functools import wraps
from typing import Any, Callable, Literal
import aiohttp
from PyQt5.QtCore import QSize
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.QtGui import QTextCursor, QPixmap
from PyQt5.QtWidgets import QMainWindow, QWidget, QTableWidget, QTableWidgetItem, QLabel, QStyle, QHBoxLayout, \
    QPushButton, QTextEdit, QLayout, QVBoxLayout, QSlider
from PyQt6.QtCore import QTimer
from qasync import QEventLoop, QApplication, asyncSlot

from first.module1.utils.automatic_module import AutomaticModule
from first.module1.utils.hand_move import Moving
from first.module1.utils.neuro_util import ModelManager
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



class MainWindow(QMainWindow, Ui_Dialog):
    @staticmethod
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

    def __init__(self):
        super().__init__()
        self.logs_queue = asyncio.Queue()
        self.logger = LogEmitter(self)
        self.robot = robot
        self.ui_init()
        self.photo_path = "new.png"
        self.model_manager = ModelManager(1, self.model_action,
                                          "/Users/egoglev/PycharmProjects/Robotics/first/module1/neuro_model/runs/detect/train6/weights/best.pt",
                                          self.photo_path,
                                          )

    def model_action(self, result: list[dict]):
        try:
            self.ui.neuro_image_field.setPixmap(QPixmap(self.photo_path))
            print("model_action",type(result), result, [res.values() for res in result])
            self.update_table(
                self.ui.neuro_objects,
                ["Фигура", "Поле"],
                [res.values() for res in result],

            )
        except Exception as e:
            print(e)



    def ui_init(self):
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.lamp = MyLamp(self.ui)
        self.auto_algorithm = AutomaticModule(self)
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
        self.ui.off_worker.clicked.connect(self.end_work_with_robot)
        self.ui.robot_power_on.clicked.connect(self._start_motion)
        self.ui.robot_start_position.clicked.connect(self.start_position)

        self.ui.flag_logs_to_csv.clicked.connect(self.log_logs_to_csv)

        self.ui.logs_field.textChanged.connect(self.log_change_text)

        self.ui.take_and_put.clicked.connect(self._take_put_motion)

        self.ui.hand_mode.clicked.connect(self._hand_mode)

        self.ui.robot_conveyer_stop.clicked.connect(self.stop_conv)
        self.ui.robot_conveyer_start.clicked.connect(self.start_conv)
        st = time.perf_counter()

        print("Время выполнения зашрузки изображения", time.perf_counter() - st)

    def log_change_text(self):
        self.ui.logs_field.moveCursor(QTextCursor.End)

    @asyncSlot()
    async def _take_put_motion(self):
        if self.ui.take_and_put.isChecked():
            await asyncio.to_thread(robot.toolON)
            self.logger.info("Захват объекта")
        else:
            await asyncio.to_thread(robot.toolOFF)
            self.logger.info("Отхват объекта")

    @asyncSlot()
    async def _hand_mode(self):
        if self.ui.hand_mode.isChecked():
            self.logger.info("Переход в ручной режим")
            await self.lamp.green()
        else:
            self.logger.info("Выход из ручного режима")
            await self.lamp.blue()


    @asyncSlot()
    async def end_work_with_robot(self):
        self.logger.info("Завершение работы с робота")
        res = await asyncio.to_thread(robot.moveToInitialPose)
        if res:
            self.logger.info("Возврат к начальной позиции")
            await self.stop_conv()
            await self.lamp.clear()
        if not res:
            self.logger.error("Отрицательный ответ от робота при возврате в начальное положение!")


    @asyncSlot()
    async def _start_motion(self):
        self.logger.info("Запуск моторов робота")
        await asyncio.to_thread(robot.engage)
        await self.lamp.blue()

    @asyncSlot()
    async def stop_(self):
        self.logger.info("Остановка робота")
        await self.auto_algorithm.end_auto()
        while True:
            res = await asyncio.to_thread(robot.disengage)
            if res:
                break
            await asyncio.sleep(.1)
        await self.stop_conv()
        self.logger.info("Полная остановка робота")
        await self.lamp.red()

    @asyncSlot()
    async def start_position(self):
        res = await asyncio.to_thread(robot.activateMoveToStart)
        if res:
            await self.lamp.blue()
            self.logger.info("Возврат к стартовой позиции")
        else:
            self.logger.error("Ощибка возврата к стартовой позиции")

    @asyncSlot()
    async def stop_conv(self): # Я робота не видел, но мне сказали, что есть конвейер, фантазеры ей богу)
        res = await asyncio.to_thread(robot.conveyer_stop)
        if res:
            self.logger.info("Остановка конвейера!")
        else:
            self.logger.error("Отрицательный ответ от возврата остановки конвейера")
        return res

    @asyncSlot()
    async def start_conv(self): # Я робота не видел, но мне сказали, что есть конвейер, фантазеры ей богу)
        res = await asyncio.to_thread(robot.conveyer_start)
        if res:
            self.logger.info("Запуск конвейера!")
        else:
            self.logger.error("Отрицательный ответ при запуске конвейера")


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
        self.update_table(
            self.ui.table_axes_joints,
            ["J1", "J2", "J3", "J4", "J5", "J6"],
            data,
            indexes=["radians", "ticks", "temperature", "degrees"],
        )
    async def update_table_position_robot_and_gripper(self):
        data = [
            await asyncio.to_thread(robot.getLinearTrackPosition)
        ]
        self.update_table(
            self.ui.table_position_robot,
            ["x", "y", "z"],
            data
        )
        state = await asyncio.to_thread(robot.getToolState)
        if state:
            self.ui.Derjatel_itema_bez_sms_i_reg.setStyleSheet("background-color: rgb(0, 120, 0);")
        else:
            self.ui.Derjatel_itema_bez_sms_i_reg.setStyleSheet("background-color: rgb(255, 255, 255);")

    async def lifespan(self):
        tasks = [
            self.update_table_axes_joints(),
            self.update_table_position_robot_and_gripper()
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
    window.model_manager.start()
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
