import sqlite3
import time
import requests
import numpy as np
import math
import cv2
import json
import sys

import database as db

def intrinsic(width, height, fov_x, fov_y):
    K = np.zeros((3, 3))
    K[0, 0] = width / (2 * math.tan(fov_x / 2))
    K[1, 1] = height / (2 * math.tan(fov_y / 2))
    K[0, 2] = width / 2
    K[1, 2] = height / 2
    K[2, 2] = 1
    return K

def modelview(width1, height1, width2, height2, fov_x, fov_y, H):
    quad_3d = np.float32([[-math.tan(fov_x / 2), -math.tan(fov_y / 2), 0],
                          [ math.tan(fov_x / 2), -math.tan(fov_y / 2), 0],
                          [ math.tan(fov_x / 2),  math.tan(fov_y / 2), 0],
                          [-math.tan(fov_x / 2),  math.tan(fov_y / 2), 0]])
    quad_2d = np.float32([[0, 0], [width2, 0], [width2, height2], [0, height2]])
    quad_2d = cv2.perspectiveTransform(quad_2d.reshape(1, -1, 2), H).reshape(-1, 2)
    K = intrinsic(width1, height1, fov_x, fov_y)
    res, rvec, tvec = cv2.solvePnP(quad_3d, quad_2d, K, None)
    rotM = cv2.Rodrigues(rvec)[0]
    cameraPosition = -np.matrix(rotM).T * np.matrix(tvec)
    cameraPosition[0,0] = -cameraPosition[0,0]
    #cameraPosition[1,0] = -cameraPosition[1,0]
    cameraPosition = cameraPosition.T * rotM
    modelview = combine_rotation_translation(rotM.T, cameraPosition)
    return modelview

def combine_rotation_translation(rotation, translation):
    matrix = np.zeros((4, 4))
    matrix[0:3, 0:3] = rotation
    matrix[0:3, 3] = translation.reshape(1, -1, 3)
    matrix[3, 3] = 1
    return matrix

def matrix_to_opengl(matrix):
    conversion = np.zeros((4, 4))
    conversion[0, 0] = 1
    conversion[1, 1] = -1
    conversion[2, 2] = -1
    conversion[3, 3] = 1
    return matrix * conversion

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

conn = db.connect()
detector, matcher = init_opencv()

if __name__ == '__main__':
    # TODO use docopt

    if len(sys.argv) >= 2 and sys.argv[1] == "offline":
        img1 = cv2.imread("neg-x.jpg", 1)
        kp1, desc1 = detector.detectAndCompute(img1, None)
        
        for file in ["photos/1", "neg-x.jpg", "neg-x-scaled.jpg", "neg-x-cropped.jpg", "neg-x-rotated.jpg", "neg-x-perspective.jpg"]:
            
            img2 = cv2.imread(file, 1)
            kp2, desc2 = detector.detectAndCompute(img2, None)
            
            h = compute_homography(kp2, desc2, kp1, desc1)
            height1, width1, channels = img1.shape
            height2, width2, channels = img2.shape
            matrix = modelview(width1, height1, width2, height2, math.radians(90), math.radians(90), h)
            #modelview(width1, height1, width2, height2, math.radians(45), math.radians(45), h)
            #modelview(width1, height1, width2, height2, math.radians(53), math.radians(40), h)
        
            # Rotate because we're comparing against the neg-x face, but our matrices are against the neg-z
            rotation = np.float32([[0, 0, -1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]])
            matrix = rotation.dot(matrix);
        
            print '{url: "../%s", id: 1, json:' % (file,)
            print json.dumps([item for sublist in matrix.tolist() for item in sublist])
            print '},'
    else:
        base_img = cv2.imread("base.jpg", 1)
        base_kp, base_desc = detector.detectAndCompute(base_img, None)
        
        id = 0
        while True:
            id, url = get_id_url(conn, id)
            print "Processing %s..." % (url,)
            try:
                img = load_img(url)
                
                kp, desc = detector.detectAndCompute(img, None)
                h = compute_homography(base_kp, base_desc, kp, desc)
                if h:
                    print "Got homography: %s" % (json.dumps(h.tolist()),)
                    set_json(conn, id, json.dumps(h.tolist()))
            except:
                print "Caught exception - skipping"
