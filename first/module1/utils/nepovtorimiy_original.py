import asyncio
import random
import threading
from math import pi
from time import sleep

from motion.robot_control import InterpreterStates


class RandomMixin:
    def random_state(self):
        sleep(.1) # как в самых нормисных курсах делаем вид что отправляем синхронный запрос к api
        return random.choice([True, True, True, True, False])

    def random_coords(self):
        sleep(.1)
        return [random.randint(1,157)/100 for _ in range(6)]


class MotionBlurRobot(RandomMixin):
    def __init__(self, *args, **kwargs):
        ...

    def manualCartMode(self):
        return self.random_state()

    def manualJointMode(self):
        return self.random_state()

    def toolON(self):
        return self.random_state()

    def toolOFF(self):
        return self.random_state()

    def engage(self):
        return self.random_state()

    def disengage(self):
        return self.random_state()

    def moveToInitialPose(self):
        return self.random_state()

    def setJointVelocity(self, p: list[float]):
        return self.random_state()

    def getMotorPositionRadians(self):
        return self.random_coords()

    def getMotorPositionTick(self):
        return self.random_coords()

    def getActualTemperature(self):
        return self.random_coords()

    def getLinearTrackPosition(self):
        return self.random_coords()

    def get_motor_degree_position(self):
        return map(lambda x: f"{x * 57.2958:.1f}", self.getMotorPositionRadians())

    def getangular_position(self):
        return self.random_coords()

    def activateMoveToStart(self):
        return self.random_state()

    def conveyer_start(self):
        return self.random_state()

    def conveyer_stop(self):
        return self.random_state()

    def getToolState(self):
        # Там не bool, ну предположу что там 0, 1 что и есть bool, а то не понятно что за состояние:
        return self.random_state()

    def addMoveToPointL(self, waypoint_list, velocity=0.1, acceleration=0.2,
                        rotational_velocity=3.18, rotational_acceleration=6.37,
                        ref_joint_coord_rad=[]) -> bool:
        return self.random_state()


    def addMoveToPointC(self, waypoint_list, angle, velocity=0.1, acceleration=0.2,
                        rotational_velocity=3.18, rotational_acceleration=6.37,
                        ref_joint_coord_rad=[]) -> bool:

        return self.random_state()


    def addMoveToPointJ(self, waypoint_list=None, rotational_velocity=pi / 4, rotational_acceleration=pi / 2) -> bool:
        return self.random_state()


    def addLinearTrackMove(self, position: float = 0.0) -> bool:
        return self.random_state()


    def addToolState(self, value: int = 0) -> bool:
        return self.random_state()


    def addWait(self, wait_time: float = 0.0) -> bool:
        return self.random_state()


    def addConveyerState(self, value: int = 0) -> bool:
        return self.random_state()


    def play(self) -> bool:
        return self.random_state()


    def pause(self) -> bool:
        return self.random_state()

    def stop(self) -> bool:
        return self.random_state()


    def reset(self) -> bool:
        return self.random_state()

    def getActualStateOut(self) -> InterpreterStates:
        return InterpreterStates.PROGRAM_IS_DONE.value

class LedLamp(RandomMixin):
    def __init__(self, ip='192.168.2.101', port=8890):
        self.__hostname = ip
        self.__port = port
        self.timeout = 0.2
        self._lock = threading.RLock() # Скопировал, смотрим как работает с асинхронностью, не ассихронная блокировка,
        # ну думаю норм, потому что ассинхронность не используется...

    def setLamp(self, status: str = "0000") -> bool:
        """
        Set light to the lamp.
            Args:
                status: status for each color

            Description:
                The status for the "state" variable is written in the sequence:
                  - 1111 to turn on all colors
                  - 0000 to turn off all colors

                - The first digit corresponds (**1**000) -> blue color
                - The second digit corresponds (0**1**00) -> green color
                - The third digit corresponds (00**1**0) -> yellow color
                - The fourth digit corresponds (000**1**) -> red color

            Returns:
                bool: True if operation succeeded, False otherwise
        """
        with self._lock:
            sleep(.5)
            print(f"ЛАМПА УСТАНОВЛЕННО {status}")
            return self.random_state()
