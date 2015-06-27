#!/usr/bin/env python

import sys
import time
import json

sys.stdout.write('Content-type: text/event-stream\r\n\r\n')

import database as db

sent = set()
conn = db.init_db()
last_id = 0

while True:

    cur = conn.cursor()

    data = []
    cur.execute('SELECT id, url, created, json FROM photos WHERE id > ? AND json IS NOT NULL ORDER BY id;', (last_id,))
    while True:
        row = cur.fetchone()
        if row is None:
            break
        id, url, created, json_text = row
        data.append({'id':id, 'url':url, 'created':created, 'json':json.loads(json_text)})
        last_id = max(id, last_id)

    if data:
        sys.stdout.write(json.dumps(data))
        sys.stdout.write('\r\n\r\n')
        sys.stdout.flush()
    time.sleep(1)

