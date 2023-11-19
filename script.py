from datetime import datetime as dt

file = r"C:\Users\heyoungHwang\dev\gardener\csv\20231118_121727.csv"

with open(file, "r") as f:
    next(f)
    for line in f:
        d, t, temp, humi = line.strip().split(",")
        Y, M, D = map(int, d.split("-"))
        h, m, s = map(int, t.split(":"))
        timestamp = dt(Y, M, D, h, m, s)
        temp, humi = float(temp), float(humi)
        print(f"{timestamp.isoformat()}, {temp}, {humi}")
