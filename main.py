#!/usr/bin/python3 
import pyfirmata
import Adafruit_DHT      # 라이브러리 불러오기
import time
from picamera import PiCamera
from os import system
import matplotlib.pyplot as plt
from matplotlib import dates as mdates

from datetime import datetime

INVALID_VALUE = 1234
PERIOD_TIME = 6

def get_curr_time():
    return time.localtime().tm_hour

def do_routine(csv_file_name:str):
    print("time has come")
    with open(csv_file_name, "r") as f:
        next(f)
        time_lst = []
        temp_lst = []
        humi_lst = []
        max_temp,min_temp = -9999, 9999
        max_humi,min_humi = -9999, 9999
        for line in f:
            if "," not in line: break
            d,t,temp,humi = line.split(",")
            Y,M,D = map(int, d.split("-"))
            h,m,s = map(int, t.split(":"))
            dt = datetime(Y,M,D,h,m,s)
            time_lst.append(dt)

            temp, humi = float(temp), float(humi)
            temp_lst.append(float(temp))
            humi_lst.append(float(humi))
            if temp != INVALID_VALUE:
                max_temp = max(max_temp, temp)
                min_temp = min(min_temp, temp)
            if humi != INVALID_VALUE:
                max_humi = max(max_humi, humi)
                min_humi = min(min_humi, humi)

        average_temp = sum(temp_lst)/len(temp_lst)
        average_humi = sum(humi_lst)/len(humi_lst)

        myFmt = mdates.DateFormatter('%H:%M')

        fig, ax1 = plt.subplots()
        fig.set_figheight(9)
        fig.set_figwidth(12)
        plt.grid(True, axis='x')
        plt.xticks(rotation=45)
        plt.title(f"{time_lst[0]}")
        
        ax1.plot(time_lst, temp_lst, color='green', label="temperature")
        ax1.plot(time_lst, [average_temp]*len(time_lst), ":", color='darkgreen', label="average")
        
        ax1.set_xticks(time_lst[::72])
        ax1.xaxis.set_major_formatter(myFmt)
        ax1.set_ylabel('Temperature')
        ax1.legend(loc="upper right")

        ax2 = ax1.twinx()
        ax2.plot(time_lst, humi_lst, color='deeppink', label="humidity")
        ax2.plot(time_lst, [average_humi]*len(time_lst), ":", color='red', label="average")
        
        ax2.set_xticks(time_lst[::72])
        ax2.xaxis.set_major_formatter(myFmt)
        ax2.set_ylabel('Humidity')
        ax2.legend(loc="lower right")
        plt.savefig(f"img/{time.strftime('%Y-%m-%d')}.jpg")

        print(f"{average_temp=:.2f}")
        print(f"{average_humi=:.2f}")

    with open(f"doc/{time.strftime('%Y-%m-%d')}.md", 'w') as md:
        md.write(f"""![some image](https://hehehwang.github.io/gardener/img/{time.strftime('%Y-%m-%d')}.jpg)\n
average temperature: {average_temp:.2f}\n
average humidity: {average_humi:.2f}\n""")
    system("git add doc/* csv/* img/*")
    commit_msg = f"write log {time.strftime('%Y-%m-%d')}"
    system(f"git commit -m {commit_msg}")
    system("git push origin master")

    with open(f"READMD.md", "w") as md:
        md.write(f"""Hello gardener!
                 Newest report: [{time.strftime('%Y-%m-%d')}](https://hehehwang.github.io/gardener/doc/{time.strftime('%Y-%m-%d')}.md)""")


def main():
    board = pyfirmata.Arduino("/dev/ttyUSB0")
    sensor = Adafruit_DHT.DHT22     #  sensor 객체 생성
    pin = 2            
                
    # camera = PiCamera()
    # camera_cntr = 0

    fan_pwm = board.get_pin('d:9:p')
    fan_pwm.write(0)

    period_time_flag = False
    logfile_name = f"csv/{time.strftime('%Y%m%d_%H%M%S')}.csv"
    with open(logfile_name, 'w') as f:
        f.write("date, time, temperature, humidity\n")

    while 1:
        if not period_time_flag and get_curr_time() == PERIOD_TIME:
            period_time_flag = True
            do_routine(logfile_name)
            logfile_name = f"csv/{time.strftime('%Y%m%d_%H%M%S')}.csv"
            with open(logfile_name, 'w') as f:
                f.write("date, time, temperature, humidity\n")
        
        if get_curr_time() == PERIOD_TIME + 1:
            period_time_flag = False

        humi, temp = Adafruit_DHT.read_retry(sensor, pin)
        humi = humi if humi is not None else INVALID_VALUE
        temp = temp if temp is not None else INVALID_VALUE
        with open(logfile_name, 'a') as f:
            f.write(f"{time.strftime('%Y-%m-%d')}, {time.strftime('%H:%M:%S')}, {temp:.2f}, {humi:.2f}\n") 

        # if camera_cntr == 0 and (6 < time.localtime().tm_hour < 20):
        #     camera.capture(f"/home/gardener/test_scripts/img_save/{time.strftime('%Y%m%d_%H%M%S')}_{temp:.0f}_{humi:.0f}.png")

        if 5 < get_curr_time() < 21:
            fan_pwm.write(0.6)
        else:
            fan_pwm.write(0)

        time.sleep(60)
        

if __name__ == "__main__":
    main()