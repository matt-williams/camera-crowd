
"""
Usage: database.py create-schema
"""

import sqlite3
from docopt import docopt

def init_db():
    conn = sqlite3.connect('example.db')
    return conn

def create_schema(conn):
    conn = init_db()
    cur = conn.cursor();
    cur.execute('CREATE TABLE photos (id INTEGER PRIMARY KEY, url TEXT NOT NULL, json TEXT NOT NULL, created TEXT NOT NULL);')
    cur.execute('CREATE INDEX photo_url_index ON photos(url);')
    conn.close()

if __name__ == '__main__':
    args = docopt(__doc__)

    if args['create-schema']:
        create_schema(conn)
