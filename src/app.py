import threading
import datetime
import time
from flask import Flask, render_template, jsonify, request, redirect, url_for
import data_crawler
import data_manager
import settings

app = Flask(
        __name__,
        template_folder=settings.template_dir,
        static_folder=settings.static_dir
    )

dm = data_manager.data_manager()

@app.route('/')
def main_page():
    recent_etfs = [{'ticker': x[0][1:], 'name': x[1]} for x in dm.get_recent_etfs(5)]
    return render_template('index.html', recent=recent_etfs)

@app.route('/', methods=['GET', 'POST'])
def route_to_etf():
    ticker = dm.name_to_ticker(request.form['etf'])
    if ticker != None:
        return redirect(url_for('etf_info', ticker=ticker[1:]))
    else:
        return render_template('404.html')

@app.route('/json/etf')
def show_etf_name():
    return jsonify(names = [name[0] for name in dm.get_every_name()])

@app.route('/etf/<ticker>')
def etf_info(ticker):
    name = dm.ticker_to_name(ticker)

    if name != None:
        return render_template(
            'etf.html',
            name = dm.ticker_to_name(ticker),
            ticker = ticker
        )
    else:
        return render_template('404.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html')

@app.route('/update_all')
def update_all():
    dc = data_crawler.data_crawler()
    tickers = dm.get_every_ticker()
    for ticker in tickers:
        ticker = ticker[0][1:]

        dc.create_price_table(ticker)
        recent_date = dm.get_recent_date(ticker)

        if recent_date == datetime.datetime(2018, 10, 5, 0, 0).date():
            print('skipping ' + ticker)
            continue
        elif recent_date == None:
            recent_date = datetime.datetime(2000, 1, 1, 0, 0)
        
        print('updating ' + ticker)

        dc.download_etf_price(ticker + '.KS', recent_date.strftime('%s'))
        price_data = dc.csv_to_dicts(dc.get_price_file_name(ticker + '.KS'))
        dc.update_price(ticker, price_data)
    

    return 'done!'


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
        
        etf_list = dc.csv_to_dicts(dc.get_etf_file_name())
        dc.update_etf_list(etf_list)
        

if __name__ == "__main__":
    download_scheduler = threading.Thread(target=update_daily_data)
    download_scheduler.start()

    app.run(host=settings.host_ip, port=80, debug=True)