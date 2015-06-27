import sqlite3
import time
import requests
import numpy as np
import cv2
import json

def init_db():
    conn = sqlite3.connect('example.db')
    return conn

def create_schema(conn):
    cur = conn.cursor();
    cur.execute('CREATE TABLE photos (id INTEGER PRIMARY KEY, url TEXT NOT NULL, json TEXT NOT NULL);');

#conn = init_db()
#create_schema(conn)
#conn.close()
#exit(1)

def get_id_url(conn, last_id):
    cur = conn.cursor()
    id = last_id
    url = None
    while url == None:
        cur.execute('SELECT id, url FROM photos WHERE id > ? ORDER BY id LIMIT 1;', (last_id,))
        id, url = cur.fetchone() or (id, None)
        if url == None:
            time.sleep(1)
    return id, url

def set_json(conn, id, json):
    cur = conn.cursor()
    cur.execute('UPDATE photos SET json=? WHERE id=?;', (json, id,))
    conn.commit()

def init_opencv():
    detector = cv2.BRISK_create()
    matcher = cv2.FlannBasedMatcher(dict(algorithm = 6,
                                         table_number = 6,
                                         key_size = 12,
                                         multi_probe_level = 1), {})
    return detector, matcher

def load_img(url):
    req = requests.get(url)
    data = np.frombuffer(req.content, dtype='uint8')
    img = cv2.imdecode(data, 1)
    return img

def filter_matches(kp1, kp2, matches, ratio = 0.75):
    mkp1, mkp2 = [], []
    for m in matches:
        if len(m) == 2 and m[0].distance < m[1].distance * ratio:
            m = m[0]
            mkp1.append( kp1[m.queryIdx] )
            mkp2.append( kp2[m.trainIdx] )
    p1 = np.float32([kp.pt for kp in mkp1])
    p2 = np.float32([kp.pt for kp in mkp2])
    kp_pairs = zip(mkp1, mkp2)
    return p1, p2, kp_pairs

def compute_homography(kp1, desc1, kp2, desc2):
    raw_matches = matcher.knnMatch(desc1, trainDescriptors = desc2, k = 2)
    p1, p2, kp_pairs = filter_matches(kp1, kp2, raw_matches)
    if len(p1) >= 4:
        h, status = cv2.findHomography(p1, p2, cv2.RANSAC, 5.0)
        return h
    return None

conn = init_db()
detector, matcher = init_opencv()
base_img = imgread("base.jpg", 1)
base_kp, base_desc = detector.detectAndCompute(base_img, None)
id = 0
while True:
    id, url = get_id_url(conn, id)
    print "Processing %s..." % (url,)
    img = load_img(url)
    
    kp, desc = detector.detectAndCompute(img, None)
    h = compute_homography(base_kp, base_desc, kp, desc)
    if h != None:
        print "Got homography: %s" % (json.dumps(h.tolist()),)
        set_json(conn, id, json.dumps(h.tolist()))
