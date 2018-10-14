import requests
import csv
import datetime
import psycopg2
import time
import re
import math

import settings

class data_crawler:
    def __init__(self):
        now = datetime.datetime.now()
        self.today = now.strftime('%Y%m%d')
        self.now_epoch = int(time.time())

        self.conn = psycopg2.connect(settings.conn_string)
        self.cur = self.conn.cursor()

    def csv_to_dicts(self, path):
        data_list = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                data_list.append(row)

        return data_list

    def get_price_file_name(self, ticker):
        return settings.data_path + 'price/' + ticker + '_price.csv'
    
    def get_etf_file_name(self):
        return settings.data_path + 'etf_list-' + self.today + '.csv'

    def download_etf_list(self):
        payload = {
            'name': 'fileDown',
            'filetype': 'csv',
            'url': 'MKD/08/0801/08012001/mkd08012001_01',
            'upclss': '00',
            'domforn': '00',
            'dom': '01',
            'forn': '02',
            'sch_word': '',
            'cntr': '',
            'midclss': '00',
            'lwclss': '00',
            'type_gubun': '00',
            'tax_tp_cd': '00',
            'isur_cd': '00000',
            'trd_dd': self.today,
            'fromdate': self.today,
            'todate': self.today,
            'gubun': '1',
            'fluc_rt': '00',
            'tot_fee': '00',
            'netasst_totamt': '00',
            'volt': '00',
            'trace_err_rt': '00',
            'divrg': '00',
            'acc_trdval': '00',
            'acc_trdvol': '00',
            'sortOpt': '',
            'sortTp': 'DESC',
            'pagePath': '/contents/MKD/08/0801/08012001/MKD08012001.jsp'
        }

        market_res = requests.get(
            'http://marketdata.krx.co.kr/contents/COM/GenerateOTP.jspx',
            params = payload
        )

        file_res = requests.get(
            'http://file.krx.co.kr/download.jspx',
            params = {'code': market_res.text}
        )

        with open(self.get_etf_file_name(), 'wb') as f:
            f.write(file_res.content)

        return len(file_res.text.split('\n'))

    def update_etf_list(self, etf_list):
        for etf in etf_list[1:]:
            ticker = etf[0]
            issuer = etf[1]
            name = etf[2]
            tracking_index = etf[3]
            inception = etf[4]
            tax_form = etf[5]
            expenses_ratio = etf[7]
            volatility = etf[11]
            category = etf[12]
            
            query = '''
                INSERT INTO etf_list (
                    ticker, issuer, name, 
                    tracking_index, inception, tax_form, 
                    expenses_ratio, volatility, category
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (ticker) DO UPDATE
                    SET 
                        issuer = EXCLUDED.issuer,
                        name = EXCLUDED.name,
                        tracking_index = EXCLUDED.tracking_index,
                        inception = EXCLUDED.inception,
                        tax_form = EXCLUDED.tax_form,
                        expenses_ratio = EXCLUDED.expenses_ratio,
                        volatility = EXCLUDED.volatility,
                        category = EXCLUDED.category;
            '''

            self.cur.execute(
                query,
                (
                    ticker, issuer, name,
                    tracking_index, inception, tax_form,
                    expenses_ratio, volatility, category
                )
            )

        self.conn.commit()

    def download_etf_price(self, ticker, from_epoch):
        price_file_name = None
        file_res = None

        while file_res is None:
            try:
                url = "https://finance.yahoo.com/quote/%s/?p=%s" % (ticker, ticker)
                cookie_res = requests.get(url)
                cookie = {'B': cookie_res.cookies['B']}
                lines = cookie_res.content.decode('unicode-escape').strip().replace('}', '\n')

                crumb_store = []
                for l in lines.split('\n'):
                    if re.findall(r'CrumbStore', l):
                        crumb_store = l

                crumb = crumb_store.split(':')[2].strip('"')

                price_file_name = self.get_price_file_name(ticker)
                file_url = "https://query1.finance.yahoo.com/v7/finance/download/%s?period1=%s&period2=%s&interval=1d&events=history&crumb=%s" % (ticker, from_epoch, self.now_epoch, crumb)
                file_res = requests.get(file_url, cookies=cookie)
            except TypeError:
                pass

        with open(price_file_name, 'wb') as f:
            for block in file_res.iter_content(1024):
                f.write(block)

    def create_price_table(self, ticker):
        query = '''
            CREATE TABLE IF NOT EXISTS price_%s (
                trading_day  date PRIMARY KEY,
                price        integer NOT NULL,
                change       integer NOT NULL,
                daily_return real NOT NULL,
                log_return   real NOT NULL
            );
        ''' % ticker

        self.cur.execute(query)
        self.conn.commit()

    def insert_price(self, ticker, date, price):
        query = '''
            SELECT price FROM price_%s ORDER BY trading_day DESC LIMIT 1;
        ''' % ticker

        self.cur.execute(query)
        recent_price = self.cur.fetchone()

        if recent_price == None:
            query = '''
                INSERT INTO price_{} (
                    trading_day, price, change, daily_return, log_return
                ) VALUES (
                    '{}', {}, 0, 0, 0
                );
            '''.format(ticker, date, price)
        else:
            recent_price = recent_price[0]
            change = price - recent_price
            daily_return = change / recent_price
            log_return = math.log(daily_return + 1)
            query = '''
                INSERT INTO price_{} (
                    trading_day, price, change, daily_return, log_return
                ) VALUES (
                    '{}', {}, {}, {}, {}
                ) ON CONFLICT (trading_day) DO UPDATE
                    SET 
                        price = EXCLUDED.price,
                        change = EXCLUDED.change,
                        daily_return = EXCLUDED.daily_return,
                        log_return = EXCLUDED.log_return;
            '''.format(ticker, date, price, change, daily_return, log_return)

        self.cur.execute(query)
        self.conn.commit()

    def update_price(self, ticker, data):
        for price in data[1:]:
            try:
                float(price[4])
            except ValueError:
                continue

            self.insert_price(ticker, price[0], int(float(price[4])))