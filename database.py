
"""
Usage: database.py create-schema
"""

import sqlite3
from docopt import docopt

def connect():
    conn = sqlite3.connect('example.db')
    return conn

def create_schema():
    conn = connect()
    cur = conn.cursor();
    cur.execute('CREATE TABLE photos (id INTEGER PRIMARY KEY, url TEXT NOT NULL, json TEXT, created TEXT NOT NULL);')
    cur.execute('CREATE INDEX photo_url_index ON photos(url);')
    conn.close()

if __name__ == '__main__':
    args = docopt(__doc__)

    if args['create-schema']:
        create_schema()
