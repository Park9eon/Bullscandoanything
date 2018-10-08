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