import pyfirmata
import Adafruit_DHT
from time import sleep
from const import *
from lib import Datamanager, get_time, do_gitwork
from datetime import datetime
from pathlib import Path


class Board:
    def __init__(self):
        self.arduino = pyfirmata.Arduino("/dev/ttyUSB0")
        self.sensor_pin_no = TEMP_HUMI_SENSOR_PIN_NO

        self.fan_pwm = self.arduino.get_pin("d:9:p")
        self.fan_pwm.write(0)

        self.prev_temp = INVALID_VALUE_FLOAT
        self.prev_humi = INVALID_VALUE_FLOAT

        y, m, _, _, _ = get_time()
        csv_filepath = Path(f"csv/{y}-{m}.csv")
        self.datamanager = Datamanager(csv_filepath)

        self.last_reported = datetime(0, 0, 0, 0, 0, 0)

    def read_sensor(self) -> tuple[float, float]:
        retry_counter = 0
        while 1:
            humi, temp = Adafruit_DHT.read_retry(Adafruit_DHT.DHT22, self.sensor_pin_no)
            temp = temp if temp is not None else INVALID_VALUE_FLOAT
            humi = humi if humi is not None else INVALID_VALUE_FLOAT

            if temp == INVALID_VALUE_FLOAT or humi == INVALID_VALUE_FLOAT:
                self.invalid_counter += 1
                return temp, humi

            if (
                self.prev_temp == INVALID_VALUE_FLOAT
                or self.prev_humi == INVALID_VALUE_FLOAT
                or abs(self.prev_temp - temp) < TEMP_TOLERANCE
                or abs(self.prev_humi - humi) < HUMI_TOLERANCE
                or 5 < retry_counter
            ):
                self.prev_temp = temp
                self.prev_humi = humi

                return temp, humi
            else:
                sleep(1)
                retry_counter += 1
                continue

    def routine(self):
        temp, humi = self.read_sensor()
        _, curr_month, curr_day, curr_hour, _ = get_time()

        if 6 < curr_hour < 21:
            self.fan_pwm.write(0.6)
        else:
            self.fan_pwm.write(0.0)

        self.datamanager.write_datum(temp, humi)
        if curr_hour == REPORT_TIME and (
            self.last_reported.day,
            self.last_reported.hour,
        ) != (curr_day, curr_hour):
            self.publish_report()
            self.last_reported = datetime.now()


def main():
    board = Board()
    while 1:
        board.routine()
        do_gitwork()
        sleep(60)