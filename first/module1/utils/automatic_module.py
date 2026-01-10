import asyncio
import json
import time
from enum import Enum
import pickle
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFileDialog, QPushButton
from qasync import asyncSlot
from pydantic import BaseModel
from motion.robot_control import Waypoint, InterpreterStates

if __name__ == '__main__':
    from first.module1.project import MainWindow

class Coordinates(Enum):
    # В теории все координаты можно получить через ручное управление и с кнопкой записать радианы которые потом сюда вставить,
    # *Мем, где человек трет ладони и ухмыляется
    # Спустя 2 часа, а может 3 и написав всё внизу и переписав сохрание 3 раза, этот механизм будет тяжело дополнять, что так себе(, но первая пытка ^_^

    UNDER_CONV_POS = Waypoint((0,0,0,0,0,0)) # Место над объектом
    TAKE_POSITION = Waypoint((0,0,0,0,0,0)) # ТИпо позиция где он возьмет объект
    TAKE_ACTION = "self.window.robot.addToolState(1)"
    PUT_ACTION = "self.window.robot.addToolState(0)"

    ROTATE_TO_PAL = Waypoint((0,0,0,0,0,0)) # Повернуть к месту где класть

    ROTATE_TO_DEF = Waypoint((0,0,0,0,0,0)) # ПОВОРОТ к мусорке

    UNDER_PALLET_1 = Waypoint((0,0,0,0,0,0))
    PUT_PALLET_1 = Waypoint((0,0,0,0,0,0))
    UNDER_PALLET_2 = Waypoint((0,0,0,0,0,0))
    PUT_PALLET_2 = Waypoint((0,0,0,0,0,0))
    UNDER_PALLET_3 = Waypoint((0,0,0,0,0,0))
    PUT_PALLET_3 = Waypoint((0,0,0,0,0,0))
    UNDER_PALLET_4 = Waypoint((0,0,0,0,0,0))
    PUT_PALLET_4 = Waypoint((0,0,0,0,0,0))

class OneAlgorithm(BaseModel):
    name: str
    actions: list[Coordinates]

    def dump(self):
        return {
            "name": self.name,
            "actions": [act.name for act in self.actions],
        }
    @classmethod
    def load(cls, **kwargs):
        kwargs["actions"] = [getattr(Coordinates, act) for act in kwargs["actions"]]
        return cls.model_validate(kwargs)


class Pallete:

    __pallete_fields = 4

    def __init__(self):
        # Будем называть места пронумерованно чтобы удобно было, не знаю зачем этот коментарий, потому что могу!
        self._pallete = {
            x:False
            for x in range(1, self.__pallete_fields + 1)
        }

    def get_space_place(self):
        for place, val in self._pallete:
            if not val:
                return place
        return None

    def is_empty(self, place):
        return not self._pallete[place]

    def put(self, place):
        self._pallete[place] = True

    def take(self, place):
        self._pallete[place] = False

    def clear(self):
        self._pallete = {
            x:False
            for x in range(1, self.__pallete_fields + 1)
        }
    def show(self):
        return self._pallete.items()


class AddToPallete(QObject):
    def __init__(self, action, name):
        super().__init__()
        print("SUPER")
        self.action = action
        self.name = name
        print("SUPER", action, name)

    def __call__(self):
        print("sad")
        return self.action(self.name)

class AutomaticModule(QObject):

    def __init__(self, window: "MainWindow"):
        super().__init__()
        print("AutomaticModule")
        self.window = window
        self.logger = window.logger
        self.pallete = Pallete()
        self.ui()
        self.__alg: list[OneAlgorithm] = []

    def ui(self):
        self.window.ui.auto_work_save.clicked.connect(self.save_alg)
        self.window.ui.auto_work_download.clicked.connect(self.download_alg)
        for key, button in self.window.ui.__dict__.items():
            if isinstance(button, QPushButton) and "pallete" in key:
                button: QPushButton
                mov = AddToPallete(self.add_alg, key)
                button.clicked.connect(mov) # ПРОБЛЕМА В ТОМ, что не работает слот
                print(key, button)

        self.window.ui.auto_work_back.clicked.connect(self.del_alg)
        self.window.ui.auto_work_start.clicked.connect(self.run)
        self.window.ui.auto_work_stop.clicked.connect(self.end_auto)
        self.window.ui.auto_pal_clear.clicked.connect(self.clear_pallete)
        self.show_pallete()
        ...

    def dumps(self):
        result = []
        for action in self.__alg:
            result.append(action.dump())
        return result
    @staticmethod
    def loads(data: list[dict[str, str]]):
        result = []
        for action in data:
            result.append(OneAlgorithm.load(**action))
        return result

    def download_alg(self):
        filename, _ = QFileDialog.getOpenFileName()
        if filename:
            with open(filename, "r") as f:
                data = self.loads(json.load(f))
                print("Загрузка", data)
                self.__alg = data
        self.show_alg()

    def save_alg(self):
        filename, _ = QFileDialog.getSaveFileName()
        if filename:
            print("Сохранение", self.__alg)
            with open(f"{filename}.txt", 'w') as f:
                json.dump(self.dumps(), f, indent=4)

    def show_alg(self):
        print([[row.name] for row in self.__alg])
        self.window.update_table(
            self.window.ui.auto_table_for_alg,
            ["Порядок действий"],
            [[row.name] for row in self.__alg]
        )

    def add_alg(self, name):
        self.logger.info("Добавление действия в алгоритм")

        if name[7:].isdigit():
            self.logger.debug(f"На палетту {name[7:]}")
            self.__alg.append(
                OneAlgorithm(
                    name=f"Товар '{name[7:]}'",
                    actions=[
                        Coordinates.UNDER_CONV_POS,
                        Coordinates.TAKE_POSITION,
                        Coordinates.TAKE_ACTION,
                        getattr(Coordinates, f"UNDER_PALLET_{name[7:]}"),
                        getattr(Coordinates, f"PUT_PALLET_{name[7:]}"),
                        Coordinates.PUT_ACTION
                    ]
                )
            )
        else:
            self.logger.debug("Брак")

            self.__alg.append(
                OneAlgorithm(
                    name=f"Брак",
                    actions=[
                        Coordinates.UNDER_CONV_POS,
                        Coordinates.TAKE_POSITION,
                        Coordinates.TAKE_ACTION,
                        Coordinates.ROTATE_TO_DEF,
                        Coordinates.PUT_ACTION
                    ]
                )
            )
        self.show_alg()

    def del_alg(self):
        self.logger.info("Удаление последнего действия")
        self.__alg.pop()
        self.show_alg()

    def run(self):
        self.logger.info("Запуск алгоритма")
        self.task = asyncio.create_task(self.runner())

    @asyncSlot()
    async def end_auto(self):
        try:
            self.task.cancel()
            await asyncio.to_thread(self.robot_all_actions_off)
        except Exception as e:
            self.logger.error("Ошибка при завершении автоматизации", e)

    async def runner(self):
        delay = 0.3
        print("runner")
        try:
            print("Запуск алгоритма", self.__alg)
            self.window.lamp.green()
            while self.__alg:
                alg: OneAlgorithm = self.__alg.pop(0)
                await asyncio.sleep(.1)
                self.logger.info("Начало выполнение действия:", alg.name)
                for action in alg.actions:
                    await asyncio.sleep(.1)
                    # self.logger.info(f"Выполнение действия {action.name}")
                    if isinstance(action.value, Waypoint):
                        if "PUT_PALLET_" in action.name:
                            if not self.pallete.is_empty(int(action.name[-1])):
                                self.logger.error(f"Следующее действие не может быть выполнено, для объекта {alg.name} нет места, возвращаюсь в начальную позицию")
                                await asyncio.to_thread(self.window.robot.moveToInitialPose)
                                await asyncio.sleep(2)
                                return
                            else:
                                self.pallete.put(int(action.name[-1]))
                                self.show_pallete()
                        print(action.value)
                        await asyncio.to_thread(self.window.robot.addMoveToPointJ, action.value)
                    else:
                        print("eval", action.value)
                        print(
                            "Результат выполнения eval:",
                            await asyncio.to_thread(self.evl, action.value)
                        )
                    self.window.robot.addWait(delay)

                self.window.robot.play()

                counter = 1

                while not await asyncio.to_thread(self.window.robot.getActualStateOut) is InterpreterStates.PROGRAM_IS_DONE.value:
                    await asyncio.sleep(.3)
                    if counter % 50 == 0:
                        raise Exception("Таймаут ожидания завершения программы!")
                    continue

                self.show_alg()
                await asyncio.sleep(1)
            self.logger.info("Завершение выполнения цикла алгоритма!")
        except asyncio.CancelledError:
            self.logger.warning("Отмена задачи выполнения алгоритма!")

        except Exception as e:

            print(e)
            self.logger.error("Ошибка при выполнении задачи автоматизации:", e)

        finally:
            self.logger.info("Последние действия работы автоматизации")
            self.window.lamp.red()
            await asyncio.to_thread(self.robot_all_actions_off)

            self.show_alg()

    def robot_all_actions_off(self):
        self.window.robot.stop()
        self.window.robot.reset()
        self.window.robot.disengage()

    def evl(self, action):
        return eval(action)

    def clear_pallete(self):
        self.pallete.clear()
        self.show_pallete()

    def show_pallete(self):
        self.window.update_table(
            self.window.ui.auto_table_pallete,
            ["Ячейки", "Загруженность"],
            self.pallete.show()
        )