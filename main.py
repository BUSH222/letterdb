from flask import Flask, render_template, send_file, request
import os
import sqlite3
import re


app = Flask(__name__)
DB_FILE = 'maindb.db'
DOCTXT_REL_DIR = 'documents-txt'
DOC_REL_DIR = 'documents'

print('Letter data loading...')

# LOAD DATA AT START
con = sqlite3.connect(DB_FILE)
cur = con.cursor()
con.row_factory = sqlite3.Row
cur.execute("SELECT * FROM letterdb")

# Data processing
DATA = cur.fetchall()
DATA.sort(key=lambda x:x[0])
DATADICT = []
for elem in DATA:
    DATADICT.append({"catalogue": elem[0], "date":elem[1], "addressee": elem[2], "keywords": elem[3], "regions":elem[4]})

print('Letter data loaded.')


def filter_data(data, filter_dict):
    filtered_data = []
    for d in data:
        match = True
        for key, value in filter_dict.items():
            if value != "" and not re.match(value.replace('*', '.*'), str(d.get(key))):
                match = False
                break
        if match:
            filtered_data.append(d)
    return filtered_data


@app.route('/')
def index():
    global DATADICT
    return render_template('index.html', data=DATADICT)


@app.route('/viewitem/<string:itemindex>')
def viewitem(itemindex):
    for s in os.listdir(DOCTXT_REL_DIR):
        if os.path.isfile(os.path.join(DOCTXT_REL_DIR, s)) and s.startswith(itemindex):
            return send_file(os.path.join(DOC_REL_DIR, f'{s.rsplit(".", 1)[0]}.doc'))
    return "NO FILE FOUND"

@app.route('/search', methods=["POST"])
def search():
    global DATADICT
    query = dict(request.form)
    print(query)
    return render_template('index.html', data=filter_data(DATADICT, query))


if __name__ == '__main__':
    app.run(debug=True)
