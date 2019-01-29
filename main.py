from flask import Flask, request, render_template, jsonify, send_from_directory
from pymongo import MongoClient
import datetime
import os
from functools import reduce
from operator import concat
import random

ON_HEROKU = "ON_HEROKU" in os.environ

# Completely different connection URL depending on whether we're local (so the database is on the same machine) or
# remote (with the database on mLab).

if ON_HEROKU:
    from credentials import db_hosted
    db = db_hosted
    uri = "mongodb://%s:%s@%s/%s" % (db.user, db.password, db.host, db.db_name)
else:
    from credentials import db_local
    db = db_local
    uri = "mongodb://%s/%s" % (db.host, db.db_name)

print(uri)

client = MongoClient(uri)
db = client[db.db_name]

app = Flask(__name__)

# Serve anything in the js directory (no template expansion):

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)

# Serve out TSV/CSV data files. (Temporary, until we get the JSON links up.)

@app.route("/data/<path:path>")
def send_data(path):
    return send_from_directory('data', path)

# Let's expand all our HTML as templates (though we won't use the templater that much):

@app.route("/")
def page():
    return render_template('index.html', data=db.my_posts.find())

@app.route("/template-example")
def tpage():
    return render_template('template-example.html')

@app.route("/heatmap")
def hpage():
    return render_template('heatmap.html')

@app.route("/tdata")
def tdpage():
    data = reduce(concat, [[[d, h, random.randint(0, 100)] for h in range(1, 25)] for d in range(1, 8)])
    return render_template('tdata.csv', data=data)

# Data transfer: bidirectional JSON endpoints:

@app.route('/exchange', methods=['POST'])
def exchange():
    json = request.get_json()
    if json['data'] == 37:
        return jsonify({ 'x' : 56, 'y' : [-200, 55], 'thirty_seven': 'YES'  })
    else:
        return jsonify({ 'x' : 56, 'y' : [-200, 55], 'z' : json['data']  })

@app.route('/add_data', methods=['POST'])
def add_data():
    json = request.get_json()
    instruction = json['instruction']
    mood = json['mood']

    id = db.my_posts.insert_one({'instruction': instruction,
                                 'mood': mood,
                                 'timestamp': datetime.datetime.utcnow()})

    print(id)
    return jsonify({'status' : 'DONE'})

# Launch (unless using Heroku machinery):

if (not ON_HEROKU) and __name__ == "__main__":
    app.run(debug=True)
