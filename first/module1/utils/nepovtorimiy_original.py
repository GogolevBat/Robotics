import asyncio
import random
import threading
from time import sleep

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
