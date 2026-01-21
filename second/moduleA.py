import asyncio
from shlex import join
from mutils.designer import Ui_MainWindow
from qasync import QApplication, QEventLoop, asyncSlot
from PyQt5.QtWidgets import QMainWindow
from mutils.lamp import Lamp
from mutils.fake_motion import RobotControl
from mutils.mlogger import Logger
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject
import csv
class State:
    handle = False

class ActionHandleMode(QObject):
    def __init__(self, win:"UltraWindow", wig: QSlider, index: int):
        super().__init__()
        self.win = win
        self.wig = wig
        self.index = index
    
    @asyncSlot()
    async def linear(self):
        vel = [.0, .0, .0, .0, .0, .0]
        vel[self.index] = .5 * (self.wig.value()-1)
        self.win.log.info(f"Линейное движение {vel}")

        await asyncio.to_thread(self.win.robot.setCartesianVelocity, vel)
        if vel[self.index] != 0:
            self.win.lamp.green()
        else:
            self.win.lamp.blue()

    @asyncSlot()
    async def joint(self):
        vel = [.0, .0, .0, .0, .0, .0]
        vel[self.index] = .5 * (self.wig.value()-1)
        self.win.log.info(f"Суставное движение {vel}")

        await asyncio.to_thread(self.win.robot.setJointVelocity, vel)
        if vel[self.index] != 0:
            self.win.lamp.green()
        else:
            self.win.lamp.blue()
    def release(self):

        self.wig.setValue(1)

class UltraWindow(Ui_MainWindow, QMainWindow):
    def __init__(self):
        super().__init__()
        self.robot = RobotControl()
        self.state = State()
        self.start_ui()

        self.count_movement = 0

    def start_ui(self):
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        self.log = Logger(self.ui.logs_field)
        self.lamp = Lamp(self.ui.lamp_state)

        self.ui.ActionsWindow.currentChanged.connect(self.change_action_window)
        self.ui.tabWidget_2.currentChanged.connect(self.change_move_window)

        self.acts = []
        for name, wig in self.ui.__dict__.items():
            if isinstance(wig, QSlider) and "slider_linear" in name:
                act = ActionHandleMode(
                    self, wig, int(name[-1])
                )
                wig.valueChanged.connect(act.linear)
                wig.sliderReleased.connect(act.release)
                self.acts.append(act)

            if isinstance(wig, QSlider) and "slider_joint" in name:
                act = ActionHandleMode(
                    self, wig, int(name[-1])
                )
                wig.valueChanged.connect(act.joint)
                wig.sliderReleased.connect(act.release)
                self.acts.append(act)


        self.ui.robot_on.clicked.connect(self.robot_start)
        self.ui.robot_off.clicked.connect(self.robot_stop)
        self.ui.robot_pause.clicked.connect(self.robot_pause)
        self.ui.start_position.clicked.connect(self.initial_pose)

        self.ui.elimination_stop.clicked.connect(self.full_stop)
        
        self.ui.robot_conv_start.clicked.connect(self.start_conv)
        self.ui.robot_conv_stop.clicked.connect(self.stop_conv)
        self.ui.robot_take.clicked.connect(self.action_take)
        self.ui.robot_untake.clicked.connect(self.action_untake)
        self.ui.clear_count_move_objects.clicked.connect(self.clear_movement)

        self.ui.save_to_file.clicked.connect(self.save_logs)

    def save_logs(self):
        dial = QFileDialog()
        filename, _ = dial.getSaveFileName()
        with open(f"{filename}.csv", "w") as f:
            wr = csv.writer(f)
            wr.writerow(["dt", "level", "message"])
            wr.writerows(self.log.logs.values())
            f.flush
            self.log.logs = {}

            
    def update_movement(self):
        self.update_table(
            self.ui.table_state_count_moveble_objects,
            ["Кол-во"],
            [[self.count_movement]],
            indexes=["Объектов распределенно"]
        )

    @asyncSlot()
    async def robot_start(self):
        self.log.info("Включение робота")
        await asyncio.to_thread(self.robot.engage)
        self.lamp.blue()
    @asyncSlot()
    async def robot_stop(self):
        self.log.info("Выключение робота")
        await asyncio.to_thread(self.robot.disengage)
        self.lamp.red()

    @asyncSlot()
    async def robot_pause(self):
        self.log.info("Пауза робота")
        await self.robot_stop()
        # await asyncio.to_thread(self.robot.disengage)
        self.lamp.yellow()

    @asyncSlot()
    async def initial_pose(self):
        self.log.info("Перемещение робота в начальную позицию")
        await asyncio.to_thread(self.robot.moveToInitialPose)
        
    @asyncSlot()
    async def full_stop(self):
        self.log.info("Принудительная остановка робота")
        await self.robot_stop()
        await self.stop_conv()
        self.lamp.red()
        
    @asyncSlot()
    async def start_conv(self):
        self.log.info("Запуск конвейера")
        await asyncio.to_thread(self.robot.conveyer_start)
        
    @asyncSlot()
    async def stop_conv(self):
        self.log.info("Остановка конвейера")
        await asyncio.to_thread(self.robot.conveyer_stop)
    
    @asyncSlot()
    async def action_take(self):
        self.log.info("Захват объекта")
        await asyncio.to_thread(self.robot.toolON)
    
    @asyncSlot()
    async def action_untake(self):
        self.log.info("Отпускание объекта")
        await asyncio.to_thread(self.robot.toolOFF)
        
        self.count_movement += 1
        self.update_movement()

    def clear_movement(self):
        self.count_movement = 0
        self.update_movement()


    @asyncSlot()
    async def change_move_window(self):
        index = self.ui.tabWidget_2.currentIndex()

        if index == 0:
            self.log.info("Включение линейного ручного управления")
            await asyncio.to_thread(self.robot.manualCartMode)
        else:
            self.log.info("Включение суставного ручного управления")
            await asyncio.to_thread(self.robot.manualJointMode)

    def change_action_window(self):
        self.state.handle = False
        index = self.ui.ActionsWindow.currentIndex()

        match index:
            case 1:
                self.state.handle = True
                self.log.info("Включение ручного управления")
                self.ui.tabWidget_2.setCurrentIndex(0)
    


    @staticmethod
    def update_table(table: QTableWidget, columns: list, matrix: list[list], indexes = None):
        table.setRowCount(len(matrix))
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        if indexes:
            table.setVerticalHeaderLabels(indexes)
        for x, line in enumerate(matrix):
            for y, el in enumerate(line):
                table.setItem(x, y, QTableWidgetItem(f"{el}"))

    async def __lifespan(self):
        mini_data = []
        mini_data.extend(await asyncio.to_thread(self.robot.getToolPosition))
        mini_data[3] = await asyncio.to_thread(self.robot.getToolState)
        
        joint_data = []
        joint_data.append(await asyncio.to_thread(self.robot.getMotorPositionTick))
        rads = await asyncio.to_thread(self.robot.getMotorPositionRadians)
        joint_data.append(rads)
        joint_data.append(map(lambda x: round(x * 57.29577, 2), rads))
        joint_data.append([await asyncio.to_thread(self.robot.getActualTemperature)] * 6)
        return mini_data, joint_data

    async def lifespan(self):

        mini_data, joint_data = await self.__lifespan()
        self.update_table(
            self.ui.table_state_mini,
            ["x", "y", "z", "gripper"],
            [mini_data]
        )
        self.update_table(
            self.ui.table_state_big,
            ["j1", "j2", "j3", "j4", "j5", "j6"],
            joint_data,
            indexes=["Тики", "Радианы", "Градусы", "Температура"]
        )



async def main(main_window: UltraWindow,event: asyncio.Event):
    while not event.is_set():
        await asyncio.sleep(3)
        await main_window.lifespan()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    main_window = UltraWindow()
    main_window.show()
    
    asyncio.run(main(main_window, app_close_event), loop_factory=QEventLoop)