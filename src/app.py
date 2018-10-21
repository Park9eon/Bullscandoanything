import threading
import datetime
import time
from flask import Flask, render_template, jsonify, request, redirect, url_for
import data_crawler
import data_manager
import settings
import math

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
    name = dm.ticker_to_name(ticker)['name']
    info = dm.ticker_to_info(ticker)
    current_price = dm.get_past_price(ticker, 0)
    recent_change = dm.get_recent_change(ticker)
    realized_vol = dm.get_realized_vol(ticker)

    change_rate = lambda x : round((current_price - x) / x * 100, 2) if x != None else '-'

    if name != None:
        return render_template(
            'etf.html',
            name = name,
            ticker = ticker,
            info = info,
            price = dm.get_past_price(ticker, 0),
            recent_date = dm.get_recent_date(ticker),
            recent_change = recent_change,
            return_1 = change_rate(dm.get_past_price(ticker, 1)),
            return_3 = change_rate(dm.get_past_price(ticker, 3)),
            return_6 = change_rate(dm.get_past_price(ticker, 6)),
            return_12 = change_rate(dm.get_past_price(ticker, 12)),
            return_ytd = change_rate(dm.get_past_price(ticker, -1)),
            return_max = change_rate(dm.get_past_price(ticker, -2)),
            realized_vol = realized_vol,
            var_90_95 = dm.get_value_at_risk(ticker, 90, 0.95),
            var_90_99 = dm.get_value_at_risk(ticker, 90, 0.99)
        )
    else:
        return render_template('404.html')

@app.route('/list/<int:page>', methods=['GET'])
def show_etf_list_get(page):
    category = request.args.get('category')
    
    if category == None:
        data = dm.get_etf_list()
        return render_template(
            'list.html',
            data = data['data'][20 * (page - 1) : 20 * page],
            page = page,
            total = (data['length'] - 1) // 20 + 1
        )
    else:
        data = dm.get_etf_list_by_category(category)
        return render_template(
            'list.html',
            data = data['data'][20 * (page - 1) : 20 * page],
            page = page,
            total = (data['length'] - 1) // 20 + 1
        )

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html')

@app.route('/update_all')
def update_all():
    update_daily_data()
    return 'done!'


def update_daily_data():
    dc = data_crawler.data_crawler()
    num_etf = dc.download_etf_list()
    if num_etf > 1:
        etf_list = dc.csv_to_dicts(dc.get_etf_file_name())
        dc.update_etf_list(etf_list)
    print('num_etf: {}'.format(num_etf))
    

    tickers = dm.get_every_ticker()

    for ticker in tickers:
        ticker = ticker[0][1:]

        dc.create_price_table(ticker)
        recent_date = dm.get_recent_date(ticker)

        if recent_date == None:
            recent_date = datetime.datetime(2000, 1, 1, 0, 0)
        
        print('updating ' + ticker)

        dc.download_etf_price(ticker + '.KS', recent_date.strftime('%s'))
        price_data = dc.csv_to_dicts(dc.get_price_file_name(ticker + '.KS'))
        dc.update_price(ticker, price_data)


def update_scheduler():
    while True:
        now = datetime.datetime.now()

        tomorrow = now + datetime.timedelta(1)
        due_time = datetime.datetime(
            year = tomorrow.year, month = tomorrow.month, day = tomorrow.day,
            hour = 0, minute = 0, second = 0
        )

        print('{} sec left...'.format((due_time - now).total_seconds()))

        time.sleep(
            (due_time - now).total_seconds()
        )

        update_daily_data()

    

if __name__ == "__main__":
    download_scheduler = threading.Thread(target=update_scheduler)
    download_scheduler.start()

    app.run(**settings.app_conn)