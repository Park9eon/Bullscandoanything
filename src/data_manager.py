import psycopg2

import settings

class data_manager:
    def __init__(self):
        self.conn = psycopg2.connect(settings.conn_string)
        self.cur = self.conn.cursor()
    
    def get_etf_name(self, ticker):
        query = '''
            SELECT name FROM etf_list WHERE ticker = '%s';
        ''' % ticker
        self.cur.execute(query)

        name = self.cur.fetchone()

        if name == None:
            return 'None'
        else:
            return name[0]