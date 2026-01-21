from sympy import EX

from .lamp import Lamp
from .mlogger import Logger
from .fake_motion import RobotControl, Waypoint
from enum import Enum
from pydantic import BaseModel
import asyncio


class InterpreterStates(Enum):
    """List of states of the interpreter state machine"""
    PROGRAM_STOP_S = 0
    PROGRAM_RUN_S = 1
    PROGRAM_PAUSE_S = 2
    MOTION_NOT_ALLOWED_S = 3
    IN_TRANSITION = 100
    PROGRAM_IS_DONE = 200


class Coordinates(Enum):
    UNDER_CONV = (.1, .0, .0, .0, .0, .0)
    TAKE = (.2, .0, .0, .0, .0, .0)
    TOOL_ON = "self.robot.addToolState(1)"
    TOOL_OFF = "self.robot.addToolState(0)"
    DELAY = "self.robot.addWait(0.5)"

    ROTATE_TO_DEFECT = (.3, .0, .0, .0, .0, .0)
    DEFECT_ = (.4, .0, .0, .0, .0, .0)

    ROTATE_TO_PALLETE = (.5, .0, .0, .0, .0, .0)
    UNDER_PALLETE = (.6, .0, .0, .0, .0, .0)

    PALLETE_1 = (.7, .0, .0, .0, .0, .0)
    PALLETE_2 = (.8, .0, .0, .0, .0, .0)
    PALLETE_3 = (.9, .0, .0, .0, .0, .0)
    PALLETE_4 = (.91, .0, .0, .0, .0, .0)

class AlghorithmAction(BaseModel):
    name: str
    action: list[Coordinates]
    def dump(self):
        return {
            "name": self.name,
            "action": list(map(lambda x: x.name, self.action))
        }
    @classmethod
    def loads(cls, data):
        return cls(
            name=data["name"],
            action=list(map(lambda x: getattr(Coordinates, x), data["action"]))
        )


class Palette:
    def __init__(self):
        self.clear()
        self.clear_statistics()

    def clear(self):
        self.places = {
                1:False,
                2:False,
                3:False,
                4:False,
                "defect": "",
            }
    
    def clear_statistics(self):
        self.count = {
                1:0,
                2:0,
                3:0,
                4:0,
                "defect": 0,
            }
    
    def show(self):
        return {
                "columns": ["Тек. состояние", "Кол-во"],
                "matrix": list(zip(self.places.values(), self.count.values())),
                "indexes": map(str, self.places.keys())
            }
    def is_empty(self, name):
        return self.places[name] == False
    
    def full(self):
        return all(map(lambda x: isinstance(x, str) or x, self.places.values()))
    
    def put(self, name):
        if name != "defect":
            if self.places[name]:
                return False
            self.places[name] = True
        self.count[name] += 1
        return True
    

class AutoMotion:
    def __init__(self, logger:Logger, robot:RobotControl, lamp: Lamp):
        self.log = logger
        self.robot = robot
        self.lamp = lamp
        self.alg: list[AlghorithmAction] = []
        self.palette = Palette()
        self.task: asyncio.Task | None = None
        self.task_done = True
        self.lock = asyncio.Lock()

    def add(self, name=""):
        if name == "defect":
            self.alg.append(
                AlghorithmAction(
                    name="БРАК",
                    action=[
                        Coordinates.TAKE,
                        Coordinates.TOOL_ON,
                        Coordinates.UNDER_CONV,
                        Coordinates.ROTATE_TO_DEFECT,
                        Coordinates.DEFECT_,
                        Coordinates.TOOL_OFF,
                        Coordinates.UNDER_CONV,
                    ]
                )                
            )      
        else:
            ind = name
            self.alg.append(
                AlghorithmAction(
                    name=f"Объект {ind}",
                    action=[
                        Coordinates.TAKE,
                        Coordinates.TOOL_ON,
                        Coordinates.UNDER_CONV,
                        Coordinates.ROTATE_TO_PALLETE,
                        getattr(Coordinates, f"PALLETE_{ind}"),
                        Coordinates.TOOL_OFF,
                        Coordinates.UNDER_CONV,
                    ]
                )         
            )

    def remove(self):
        if len(self.alg):
            self.alg.pop()

    def clear(self):
        self.alg = []
    
    def show(self):
        return {
                "columns": ["Действие"],
                "matrix":[[alg.name] for alg in self.alg]
            }
    
    def one_action(self, index: int):
        actions = self.alg[index]
        after_pallete = None
        self.log.info(f"Выполнение дейстия: {actions.name}")
        print(actions)
        for act in actions.action:
            print(act.name)
            
            if "PALLETE_" in act.name:
                
                if not self.palette.is_empty(int(act.name[-1])):
                    self.log.info("На паллете больше нет места для объекта")
                    return None
                after_pallete = int(act.name[-1])

            if "DEFECT_" in act.name:
                after_pallete = "defect"
                
            if isinstance(act.value, tuple):
                self.robot.addMoveToPointJ(Waypoint(act.value))
            elif isinstance(act.value, str):
                eval(act.value)
            else:
                self.log.erorr("one_action Ошибка данных", act.value)

            self.robot.addWait(.4)
        return after_pallete

    async def stop(self):
        try:
            self.task.cancel()
        except:
            print()

    async def start(self):
        async with self.lock:
            if self.task_done:
                self.log.info("Запуск алгоритма автоматизации")
                self.task = asyncio.create_task(self.runner())
            else:
                self.log.warning("Нельзя запустить несколько алгоритмов подряд")
            await asyncio.sleep(.2)

    async def runner(self):
        try:
            self.task_done = False
            index = 0
            state = False
            while len(self.alg) > index:
                
                if self.palette.full():
                    state = not state
                    if state:
                        self.log.info("Паллета заполнена")
                        self.lamp.red()
                    else:
                        self.lamp.clear()
                    await asyncio.sleep(1.5)
                    continue

                self.lamp.green()

                await asyncio.to_thread(self.robot.reset)
                
                after_pallete = await asyncio.to_thread(self.one_action, index)
                index += 1
                
                if after_pallete is None:
                    self.log.info("Заполенна ячейка не получиться положить объект")
                    break

                while not(await asyncio.to_thread(self.robot.getActualStateOut) is InterpreterStates.PROGRAM_IS_DONE.value):
                    await asyncio.sleep(.2)
                self.log.debug("Установка объекта на поле", after_pallete)
                if after_pallete:
                    self.palette.put(after_pallete)

            
            await asyncio.to_thread(self.robot.reset)
            self.log.info("Завершение автоматизации, возврат к начальной позиции!")
            await asyncio.to_thread(self.robot.moveToInitialPose)

        except asyncio.CancelledError:
            self.log.info("Принудительная остановка выполнения алгоритма") 
        except Exception as e:
            self.log.error("Ошибка алгоритма", e)

        finally:
            self.task_done = True
            self.lamp.blue()

    def dumps(self):
        data = []
        for al in self.alg:
            data.append(al.dump())
        return data

    def loads(self, data: list[dict]):
        result = []
        for dt in data:
            result.append(AlghorithmAction.loads(dt))
        self.alg = result