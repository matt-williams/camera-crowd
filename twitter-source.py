
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
import traceback
import logging

from docopt import docopt

import database as db

logger = logging.getLogger(__name__)

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
        ents = data.get('entities', {}).get('media', [])
        if ents:
            for ent in ents:
                try:
                    if original:
                        created_at = parse_date(data['created_at'])
                        url = ent['media_url']
                        conn = db.connect()
                        cur = conn.cursor() 
                        cur.execute('SELECT * from photos WHERE url=?;', (url,))
                        if cur.fetchone() is None:
                            cur.execute('INSERT INTO photos(url, created) VALUES (?, ?);',
                                        (url, created_at.isoformat()))
                            logger.info("Added tweet: %s", url)
                        else:
                            logger.info("Not adding: tweet is already there")
                        conn.commit()
                        conn.close()
                    else:
                        logger.info("Not adding: tweet is not original")
                except Exception:
                    logger.exception("Unexpected exception")
        else:
            logger.info("Not adding: tweet has no media")

    except Exception:
        logger.exception("Unexpected exception")

class StdOutListener(StreamListener):

    def on_data(self, data):
        #print data
        extract_media_url(json.loads(data))
        return True

    def on_error(self, status):
        print status

if __name__ == '__main__':
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.INFO)
    args = docopt(__doc__)
    keys = json.loads(open(os.path.join(os.environ['HOME'], '.twitter-keys')).read())
    l = StdOutListener()
    auth = OAuthHandler(keys['consumer_key'], keys['consumer_secret'])
    auth.set_access_token(keys['access_token'], keys['access_token_secret'])
    api = API(auth)
    logger.info("Connected to twitter.  Scanning recent tweets.")
    for status in api.search(args['<search-term>']):
        extract_media_url(status._json)
    logger.info("Waiting for new tweets.")
    stream = Stream(auth, l)
    stream.filter(track=[args['<search-term>']])

