import threading
import datetime
import time
from flask import Flask
import data_crawler
import data_manager
import settings

app = Flask(__name__)

dm = data_manager.data_manager()

@app.route("/etf/<ticker>")
def show_etf_info(ticker):
    return dm.get_etf_name(ticker)

def update_daily_data():
    while True:
        now = datetime.datetime.now()
        dc = data_crawler.data_crawler()

        tomorrow = now + datetime.timedelta(1)
        due_time = datetime.datetime(
            year = tomorrow.year, month = tomorrow.month, day = tomorrow.day,
            hour = 23, minute = 0, second = 0
        )

        time.sleep(
            (due_time - now).total_seconds()
        )

        num_etf = dc.download_etf_list()
        if num_etf <= 1:
            continue
        
        etf_list = dc.csv_to_dicts(dc.etf_file)
        dc.update_etf_list(etf_list)
        

if __name__ == "__main__":
    download_scheduler = threading.Thread(target=update_daily_data)
    download_scheduler.start()

    app.run(host=settings.host_ip, port=80)