
"""
Usage: twitter-source.py <search-term>
"""

from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import API

import os
import json

from docopt import docopt

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
            except Exception:
                pass
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

