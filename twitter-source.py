
"""
Usage: twitter-source.py <search-term>
"""

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import API

import os
import json
import datetime
import subprocess

from docopt import docopt

import database as db


def parse_date(date):
    # python2.6 is too dumb to parse twitter's idiotic date format
    unixtime_str = subprocess.check_output(["date", "-d", date, "+%s"])
    return datetime.datetime.fromtimestamp(int(unixtime_str))    

def extract_media_url(data):
    try:
        original = True
        if 'retweeted_status' in data:
            if data['retweeted_status']['created_at'] != data['created_at']:
                original = False
        for ent in data['entities']['media']:
            try:
                if original:
                    print data['created_at'], ent['media_url']
                    created_at = parse_date(data['created_at'])
                    url = ent['media_url']
                    conn = db.init_db()
                    cur = conn.cursor() 
                    cur.execute('SELECT * from photos WHERE url=?;', (url,))
                    if cur.fetchone() is None:
                        cur.execute('INSERT INTO photos(url, created) VALUES (?, ?);',
                                    (url, created_at.isoformat()))
                    conn.commit()
                    conn.close()

            except Exception as e:
                print e
    except Exception:
        pass

class StdOutListener(StreamListener):

    def on_data(self, data):
        #print data
        extract_media_url(data)
        return True

    def on_error(self, status):
        print status

if __name__ == '__main__':
    args = docopt(__doc__)
    keys = json.loads(open(os.path.join(os.environ['HOME'], '.twitter-keys')).read())
    l = StdOutListener()
    auth = OAuthHandler(keys['consumer_key'], keys['consumer_secret'])
    auth.set_access_token(keys['access_token'], keys['access_token_secret'])
    api = API(auth)
    for status in api.search(args['<search-term>']):
        extract_media_url(status._json)
    stream = Stream(auth, l)
    stream.filter(track=[args['<search-term>']])

