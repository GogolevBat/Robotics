import asyncio
from shlex import join
from mutils.designer import Ui_MainWindow
from qasync import QApplication, QEventLoop, asyncSlot
from PyQt5.QtWidgets import QMainWindow
from mutils.lamp import Lamp
from mutils.fake_motion import RobotControl
from mutils.automatic import AutoMotion
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject
from moduleA import UltraWindow
import json

class ActionAuto(QObject):
    def __init__(self, win: "ModuleBWindow", name: str):
        super().__init__()
        self.win=win
        self.name=name

    def action(self):
        self.win.algorithm.add(self.name)

class ModuleBWindow(UltraWindow):
    def __init__(self):
        super().__init__()
        
    def start_ui(self):
        super().start_ui()
        self.algorithm = AutoMotion(self.log, self.robot, self.lamp)
        self.auto_acts = [
            ActionAuto(self, 1),
            ActionAuto(self, 2),
            ActionAuto(self, 3),
            ActionAuto(self, 4),
            ActionAuto(self, "defect")
        ]
        self.ui.auto_pallete_1.clicked.connect(self.auto_acts[0].action)
        self.ui.auto_pallete_2.clicked.connect(self.auto_acts[1].action)
        self.ui.auto_pallete_3.clicked.connect(self.auto_acts[2].action)
        self.ui.auto_pallete_4.clicked.connect(self.auto_acts[3].action)
        self.ui.auto_pallete_deffect.clicked.connect(self.auto_acts[4].action)

        self.ui.auto_pallete_delete.clicked.connect(self.delete_action)
        self.ui.auto_pallete_clear.clicked.connect(self.clear_alghorithm)

        self.ui.auto_start.clicked.connect(self.start_automatic)

        self.ui.auto_clear_state.clicked.connect(self.auto_clear_state)
        self.ui.auto_new_pallete.clicked.connect(self.auto_new_pallete)

        self.ui.auto_alg_save.clicked.connect(self.auto_alg_save)
        self.ui.auto_alg_download.clicked.connect(self.auto_alg_download)

    @asyncSlot()
    async def robot_stop(self):
        await super().robot_stop()
        await self.algorithm.stop()

    def auto_alg_save(self):
        dial = QFileDialog()
        filename, _ = dial.getSaveFileName()
        if not filename:
            return
        with open(f"{filename}.json", "w") as f:
            json.dump(self.algorithm.dumps(), f, indent=4, ensure_ascii=False)
        

    def auto_alg_download(self):
        dial = QFileDialog()
        filename, _ = dial.getOpenFileName()
        if not filename:
            return
        print(filename)
        with open(f"{filename}", "rb") as f:
            self.algorithm.loads(json.load(f))
        

    def auto_new_pallete(self):
        self.algorithm.palette.clear()
    
    def auto_clear_state(self):
        self.algorithm.palette.clear_statistics()

    @asyncSlot()
    async def start_automatic(self):
        await self.algorithm.start()

    def delete_action(self):
        self.algorithm.remove()
    def clear_alghorithm(self):
        self.algorithm.clear()

    async def lifespan(self):
        await super().lifespan()
        self.update_table(
            self.ui.auto_table_algorithm,
            **self.algorithm.show()
        )
        self.update_table(
            self.ui.auto_table_pallete_state,
            **self.algorithm.palette.show()
        )

async def main(main_window: ModuleBWindow, event: asyncio.Event):
    while not event.is_set():
        await asyncio.sleep(.5)
        await main_window.lifespan()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    main_window = ModuleBWindow()
    main_window.show()
    
    asyncio.run(main(main_window, app_close_event), loop_factory=QEventLoop)