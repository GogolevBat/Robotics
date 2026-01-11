import asyncio
import os
import time
import random

import cv2
from ultralytics import YOLO
from multiprocessing import Process, Queue
from enum import Enum

# class CoordinatesThings(Enum):
fields = {
    "FIELD_1": (287, 357),
    "FIELD_2": (470, 357),
    "FIELD_3": (530, 357),
    "FIELD_4": (260, 457),
    "FIELD_5": (450, 475),
    "FIELD_6": (630, 470),
    "FIELD_7": (223, 601),
    "FIELD_8": (440, 601),
    "FIELD_9": (667, 625),
}

class ModelWorker:
    def __init__(self, queue: Queue, model_path, file_path, *, conf=.7, ismain=False):
        self.queue = queue
        self.ismain = ismain
        self.model = YOLO(model_path)
        self.conf = conf
        self.file_path = file_path
        # self.a = self.model.names

    def predict(self, img_path: str):
        img = cv2.imread(img_path)
        results = self.model.predict(img, conf=self.conf)
        result = results[0]
        return_data = []
        for conf, cls, box in zip(
                result.boxes.conf.cpu().numpy(),
                result.boxes.cls.cpu().numpy(),
                result.boxes.xyxy.cpu().numpy().astype(int)
        ):
            x1, y1, x2, y2 = box
            cv2.rectangle(
                img,
                (x1, y1), (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.putText(
                img,
                f"{self.model.names[int(cls)]} ({conf:.2f})",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_DUPLEX,
                .8,
                (0, 0, 255)
            )

            cv2.imwrite(self.file_path, cv2.resize(img, (400, 271)))

            return_data.append({
                "name": self.model.names[int(cls)],
                "field": self.nearest(((x1+x2)/2, (y1+y2)/2))
            })
        return return_data

    def nearest(self, center: tuple):
        top_lenght = 10000
        fields_name = ""
        for key, value in fields.items():
            lenght = ((center[0] - value[0]) ** 2 + (center[1] - value[1]) ** 2) ** .5
            if lenght < top_lenght:
                top_lenght = lenght
                fields_name = key
        return fields_name

    def _procces(self):
        path = self.get_image()
        result = self.predict(path)

        if self.ismain:
            self.queue.put(result)

    def __call__(self):
        while 1:

            print("Работа")
            st = time.perf_counter()
            self._procces()
            sleep = (5 - (time.perf_counter() - st))
            print(f"Время работы: {5 - sleep}")
            if sleep > 0:
                time.sleep(sleep)

    def get_image(self):
        path = "/Users/egoglev/PycharmProjects/Robotics/first/module1/neuro_model/project-1-at-2026-01-11-09-36-8517fae7/train/images"
        file = random.choice(os.listdir(path))
        return f"{path}/{file}"

class ModelManager:
    def __init__(self, workers = 1, action=..., *args, **kwargs):
        self.flag_active = False
        self.action = action
        self.predicted_information: list[dict] = []
        self.queue = Queue()
        workers = 1 # ЛОгика доработана не будет - надежда на увеличение fps вывода изображения, времени не хватит, либо дальше будет лень
        try:
            self.processes = [
                Process(
                    target=ModelWorker(self.queue, *args, **kwargs, ismain=(i==0)),
                )
                for i in range(workers)
            ]
            for proc in self.processes:
                proc.start()
        except:
            print("=" * 60)
            print("ОШИБКА ПРИ ЗАПУСКЕ НЕЙРОСЕТИ".center(60))
            print("=" * 60)




    def close(self):
        for proc in self.processes:
            proc.terminate()

    def start(self):
        self.task = asyncio.create_task(self.taker_information())


    async def taker_information(self):
        while 1:
            data = await asyncio.to_thread(self.queue.get)
            print("ответная дата" ,data)
            self.action(data)