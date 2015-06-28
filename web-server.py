from flask import Flask, Response
import requests
import database as db
import json
import time

app = Flask(__name__)

@app.route("/photos/<id>")
def photos(id):
    conn = db.connect()
    cur = conn.cursor()
    cur.execute('SELECT url FROM photos WHERE id = ?', (id,))
    row = cur.fetchone()
    conn.close()
    if row:
        url = row[0]
        print "Proxying request for image %s to %s " % (id, url)
        rsp = requests.get(url, stream=True)
        headers = dict(rsp.headers)
        if rsp.status_code == 200:
            def gen():
                for chunk in rsp.iter_content(4096):
                    yield chunk
            return Response(gen(), headers = headers), rsp.status_code
    return "", 404

@app.route("/events")
def events():
    def gen():
        last_id = 0
        conn = db.connect()
        cur = conn.cursor()
        try:
            while True:
                data = []
                cur.execute('SELECT id, url, created, json FROM photos WHERE id > ? AND json IS NOT NULL ORDER BY id;', (last_id,))
                while True:
                    row = cur.fetchone()
                    if row is None:
                        break
                    id, url, created, json_text = row
                    data.append({'id':id, 'url':"/photos/" + id, 'created':created, 'json':json.loads(json_text)})
                    last_id = max(id, last_id)

                if data:
                    event = json.dumps(data)
                    print "Sending event %s" % (event,)
                    yield "data: %s\n\n" % (event,)
                time.sleep(1)

        except GeneratorExit:
            pass
        conn.close()

    return Response(gen(), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10080, threaded=True, debug=False)
