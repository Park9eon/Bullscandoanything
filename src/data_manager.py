import psycopg2

import settings

class data_manager:
    def __init__(self):
        self.conn = psycopg2.connect(settings.conn_string)
        self.cur = self.conn.cursor()
    
    def get_etf_name(self, ticker):
        query = '''
            SELECT name FROM etf_list WHERE ticker = '{}';
        '''.format(ticker)
        
        self.cur.execute(query)
        name = self.cur.fetchone()

        if name == None:
            return 'None'
        else:
            return name[0]

    def get_every_ticker(self):
        query = '''
            SELECT ticker FROM etf_list;
        '''

        self.cur.execute(query)
        tickers = self.cur.fetchall()

        return tickers
    
    def get_every_name(self):
        query = '''
            SELECT name FROM etf_list;
        '''

        self.cur.execute(query)
        names = self.cur.fetchall()

        return names

    def get_recent_date(self, ticker):
        query = '''
            SELECT trading_day FROM price_{} ORDER BY trading_day DESC LIMIT 1;
        '''.format(ticker)

        self.cur.execute(query)
        date = self.cur.fetchone()

        if date == None:
            return None
        else:
            return date[0]

    def get_recent_etfs(self, limit):
        query = '''
            SELECT ticker, name FROM etf_list ORDER BY inception DESC LIMIT {}
        '''.format(limit)

        self.cur.execute(query)
        etfs = self.cur.fetchall()

        return etfs

    def name_to_ticker(self, name):
        query = '''
            SELECT ticker FROM etf_list WHERE name='{}';
        '''.format(name)
        
        self.cur.execute(query)
        ticker = self.cur.fetchone()
    
        if ticker == None:
            return None
        else:
            return ticker[0]
    
    def ticker_to_info(self, ticker):
        query = '''
            SELECT issuer, tracking_index, inception, tax_form, expenses_ratio, category FROM etf_list WHERE ticker='{}';
        '''.format('A' + ticker)

        self.cur.execute(query)
        ret = self.cur.fetchone()

        if ret == None:
            return None
        else:
            info = {
                'issuer': ret[0],
                'tracking_index': ret[1],
                'inception': ret[2],
                'tax_form': ret[3],
                'expenses_ratio': ret[4],
                'category': ret[5]
            }
            return info
    
    def ticker_to_name(self, ticker):
        query = '''
            SELECT name FROM etf_list WHERE ticker='{}';
        '''.format('A' + ticker)
        
        self.cur.execute(query)
        name = self.cur.fetchone()
    
        if name == None:
            return None
        else:
            return name[0]
    
    def get_past_price(self, ticker, term):
        if term == -2:
            query = '''
                SELECT price FROM price_{} ORDER BY trading_day ASC LIMIT 1;
            '''.format(ticker)
        elif term == -1:
            query = '''
                SELECT price FROM price_{}
                WHERE trading_day <= date_trunc('year', (SELECT trading_day FROM price_{} ORDER BY trading_day DESC LIMIT 1))
                ORDER BY trading_day DESC
                LIMIT 1;
            '''.format(ticker, ticker)
        elif term == 0:
            query = '''
                SELECT price FROM price_{} ORDER BY trading_day DESC LIMIT 1;
            '''.format(ticker)
        else:
            query = '''
                SELECT price FROM price_{}
                WHERE trading_day <= (SELECT trading_day - interval '{}' month FROM price_{} ORDER BY trading_day DESC LIMIT 1)
                ORDER BY trading_day DESC
                LIMIT 1;
            '''.format(ticker, term, ticker)
        
        self.cur.execute(query)
        price = self.cur.fetchone()

        if price == None:
            return None
        else:
            return price[0]
    
    def get_recent_change(self, ticker):
        query = '''
            SELECT change, daily_return FROM price_{} ORDER BY trading_day DESC LIMIT 1;
        '''.format(ticker)

        self.cur.execute(query)
        data = self.cur.fetchone()

        if data == None:
            return None
        else:
            return {'change': data[0], 'return': round(data[1] * 100, 2)}

    def get_etf_list(self, page, amount):
        query = '''
            SELECT
                ticker, name, inception, expenses_ratio, category
            FROM etf_list ORDER BY inception DESC LIMIT {} OFFSET {};
        '''.format(amount, (page - 1) * amount)

        self.cur.execute(query)
        data = self.cur.fetchall()

        if data == None:
            return None
        else:
            return data