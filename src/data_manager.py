import psycopg2
import math

import settings

class data_manager:
    def __init__(self):
        self.conn = psycopg2.connect(settings.conn_string)
        self.cur = self.conn.cursor()

    def fetch_data(self, query, names):
        self.cur.execute(query)
        data = self.cur.fetchone()

        if data == None:
            return None
        else:
            return dict(zip(names, data))

    def fetch_many_data(self, query, names):
        self.cur.execute(query)
        data = self.cur.fetchall()

        if data == None:
            return None
        else:
            return {
                'length': len(data),
                'data': [dict(zip(names, datum)) for datum in data]
            }
    
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

        return self.fetch_data(query, [
            'issuer', 'tracking_index', 'inception', 'tax_form', 'expenses_ratio', 'category'
        ])

    def ticker_to_name(self, ticker):
        query = '''
            SELECT name FROM etf_list WHERE ticker='{}';
        '''.format('A' + ticker)

        return self.fetch_data(query, [
            'name'
        ])
    
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
            WITH price_table AS (
                SELECT
                    trading_day,
                    price,
                    lag(price, 1) 
                        OVER (ORDER BY trading_day)
                        AS price_yesterday
                FROM
                    price_{}
                GROUP BY
                    trading_day
                ORDER BY
                    trading_day DESC
            )
            SELECT 
                trading_day,
                price,
                price - price_yesterday AS change,
                (price - price_yesterday) / price_yesterday::real AS change_rate,
                ln((price - price_yesterday) / price_yesterday::real + 1) AS log_rate
            FROM price_table LIMIT 1;
        '''.format(ticker)

        return self.fetch_data(query, [
            'trading_day',
            'price',
            'change',
            'return',
            'log_return'
        ])

    def get_etf_list(self):
        query = '''
            SELECT ticker, name, inception, expenses_ratio, category
            FROM etf_list ORDER BY inception DESC;
        '''

        return self.fetch_many_data(query, [
            'ticker',
            'name',
            'inception',
            'expenses_ratio',
            'category'
        ])

    def get_etf_list_by_category(self,  category):
        query = '''
            SELECT ticker, name, inception, expenses_ratio, category
            FROM etf_list WHERE (
                category LIKE '{}-%' OR
                category LIKE '%-{}-%' OR
                category LIKE '%-{}'
            )
            ORDER BY inception DESC;
        '''.format(category, category, category)

        return self.fetch_many_data(query, [
            'ticker',
            'name',
            'inception',
            'expenses_ratio',
            'category'
        ])

    def get_realized_vol(self, ticker):
        query = '''
            WITH price_table AS (
                SELECT
                    trading_day,
                    price,
                    lag(price, 1) 
                        OVER (ORDER BY trading_day)
                        AS price_yesterday
                FROM
                    price_{}
                GROUP BY
                    trading_day
                ORDER BY
                    trading_day DESC
                LIMIT 90
            )
            SELECT 
                100 * sqrt(252 / least(count(trading_day), 90) * sum(power(ln((price - price_yesterday) / price_yesterday::real + 1),2))) AS log_rate
            FROM price_table;
        '''.format(ticker)

        return self.fetch_data(query, [
            'vol'
        ])
    
    def get_value_at_risk(self, ticker, days, z_score):
        query = '''
        WITH price_table AS (
            SELECT
                trading_day,
                price,
                lag(price, {}) 
                    OVER (ORDER BY trading_day)
                    AS price_past
            FROM
                price_{}
            GROUP BY
                trading_day
            ORDER BY
                trading_day DESC
        )
        SELECT 
            avg(ln((price - price_past) / price_past::real + 1)) AS log_rate_mean,
            stddev(ln((price - price_past) / price_past::real + 1)) AS log_rate_st
        FROM price_table;
        '''.format(days, ticker)

        try:
            stats = self.fetch_data(query, ['mean', 'std'])
            return (1 - math.exp(stats['mean'] - z_score * stats['std']))
        except TypeError:
            return '-'
