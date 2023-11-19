from datetime import datetime
from pathlib import Path
from const import *
from matplotlib import dates as mdates
from matplotlib import pyplot as plt
from os import system as sysmsg


def get_time() -> tuple[int, int, int, int, int]:
    n = datetime.now()
    return n.year, n.month, n.day, n.hour, n.minute


class Datamanager:
    def __init__(self, csvpath: Path) -> None:
        self.csv_file_path = csvpath
        if not csvpath.exists():
            with open(csvpath, "w") as f:
                f.write("timestamp, temperature, humidity\n")

    def write_datum(self, temp: float, humi: float):
        curr = datetime.now()
        timestamp = curr.replace(second=0, microsecond=0)
        with open(self.csv_file_path, "a") as f:
            f.write(f"{timestamp.isoformat()}, {temp:.2f}, {humi:.2f}\n")

    def gather_past_data(
        self, reference: datetime = datetime.now(), days: int = 1
    ) -> tuple[
        dict[datetime, tuple[float, float]], float, float, float, float, float, float
    ]:
        now_ref = reference
        past_ref = now_ref.replace(day=now_ref.day - days)

        data = {}
        timestamp_lst, temp_lst, humi_lst = [], [], []
        temp_max, temp_min = -9999.0, 9999.0
        humi_max, humi_min = -9999.0, 9999.0
        with open(self.csv_file_path, "r") as f:
            next(f)  # skip headline
            for line in f:
                if "," not in line:
                    continue
                timestamp_raw, temp_raw, humi_raw = line.split(",")
                timestamp_dt = datetime.fromisoformat(timestamp_raw)
                if timestamp_dt < past_ref:
                    continue
                temp, humi = float(temp_raw), float(humi_raw)
                data[timestamp_dt] = (temp, humi)

                if temp == INVALID_VALUE_FLOAT or humi == INVALID_VALUE_FLOAT:
                    continue

                timestamp_lst.append(timestamp_dt)
                temp_lst.append(temp)
                humi_lst.append(humi)

                temp_max = max(temp_max, temp)
                temp_min = min(temp_min, temp)
                humi_max = max(humi_max, humi)
                humi_min = min(humi_min, humi)

        temp_avg = sum(temp_lst) / len(temp_lst)
        humi_avg = sum(humi_lst) / len(humi_lst)

        return data, temp_min, temp_avg, temp_max, humi_min, humi_avg, humi_max

    def publish_report(self):
        (
            data,
            temp_min,
            temp_avg,
            temp_max,
            humi_min,
            humi_avg,
            humi_max,
        ) = self.gather_past_data()
        y, m, d, h, _ = get_time()
        filename = f"{y}-{m}-{d}_{h}"
        report_filepath = Path(f"doc/{filename}.md")
        plot_and_save_temp_humi(data, temp_avg, humi_avg, Path(f"img/{filename}.png"))

        with open(report_filepath, "w") as md:
            md.write(f"![some image]({WEBPAGE_IMG_URL}/{filename}.png)\n\n")
            md.write(
                f"Temperature: {temp_min:.2f} < {temp_avg:.2f} < {temp_max:.2f}\n\n"
            )
            md.write(f"Humidity: {humi_min:.2f} < {humi_avg:.2f} < {humi_max:.2f}\n\n")
        write_mainpage()


def roll_data(data: list[float], window: int = 30):
    total_data_cnt = len(data)
    new_data = []
    chunk = 0
    for i in range(window):
        chunk += data[i]
        new_data.append(round(chunk / (i + 1), 2))
    for prev_idx in range(total_data_cnt - window):
        now_idx = prev_idx + window
        chunk += data[now_idx]
        chunk -= data[prev_idx]
        new_data.append(round(chunk / window, 2))
    return new_data


def plot_and_save_temp_humi(
    temp_humi_data: dict[datetime, tuple[float, float]],
    temp_avg: float,
    humi_avg: float,
    save_path: Path,
):
    myFmt = mdates.DateFormatter("%H:%M")

    fig, ax1 = plt.subplots()
    fig.set_figheight(6)
    fig.set_figwidth(9)
    # fig.set_dpi(100)
    plt.grid(True, axis="x")
    plt.xticks(rotation=45)

    timestamp_lst, temp_lst, humi_lst = [], [], []
    for timestamp, v in temp_humi_data.items():
        temp, humi = v
        timestamp_lst.append(timestamp)
        temp_lst.append(temp)
        humi_lst.append(humi)

    plt.title(f"{timestamp_lst[0]}")

    ax1.plot(timestamp_lst, roll_data(temp_lst), color="green", label="temperature")
    ax1.plot(
        timestamp_lst,
        [temp_avg] * len(timestamp_lst),
        ":",
        color="darkgreen",
        label="average",
    )
    ax1.set_xticks(timestamp_lst[::72])
    ax1.xaxis.set_major_formatter(myFmt)
    ax1.set_ylabel("Temperature")
    ax1.legend(loc="upper right")

    ax2 = ax1.twinx()
    ax2.plot(timestamp_lst, roll_data(humi_lst), color="deeppink", label="humidity")
    ax2.plot(
        timestamp_lst,
        [humi_avg] * len(timestamp_lst),
        ":",
        color="red",
        label="average",
    )

    ax2.set_xticks(timestamp_lst[::72])
    ax2.xaxis.set_major_formatter(myFmt)
    ax2.set_ylabel("Humidity")
    ax2.legend(loc="lower right")

    plt.savefig(save_path, dpi=200)


def write_mainpage(readme: Path = "README.md"):
    doc_filelist = [f.stem for f in sorted(Path("doc").iterdir())][::-1]
    with open(readme, "w") as md:
        md.write(f"Hello gardener!\n\n# Report list\n\n")
        for filename in doc_filelist:
            md.write(f"* [{filename}]({WEBPAGE_DOC_URL}/{filename})\n")


def do_gitwork():
    sysmsg("git add README.md doc/* csv/* img/*")
    commit_msg = f"write log {datetime.now().strftime('%Y-%m-%d')}"
    sysmsg(f'git commit -m "{commit_msg}"')
    sysmsg("git push origin master")


if __name__ == "__main__":
    # test
    dm = Datamanager(Path("csv/test.csv"))
    dm.publish_report()
