import requests
import csv
import datetime
import psycopg2

import settings

class data_crawler:
    def __init__(self):
        now = datetime.datetime.now()
        self.today = now.strftime('%Y%m%d')
        self.etf_file = settings.data_path + 'etf_list-' + self.today + '.csv'

        self.conn = psycopg2.connect(settings.conn_string)
        self.cur = self.conn.cursor()

    def csv_to_dicts(self, path):
        data_list = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                data_list.append(row)

        return data_list

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

        with open(self.etf_file, 'wb') as f:
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
