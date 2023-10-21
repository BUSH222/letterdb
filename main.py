from flask import Flask, render_template, send_file
import os
import sqlite3


app = Flask(__name__)
DB_REL_DIR = 'db' # fix later
DOCTXT_REL_DIR = 'documents-txt'
DOC_REL_DIR = 'documents'
# LOAD DATA AT START
print('Letter data loading...')
con = sqlite3.connect("maindb.db")
cur = con.cursor()
con.row_factory = sqlite3.Row
cur.execute("SELECT * FROM letterdb")
DATA = cur.fetchall()
#DATA.sort(key=lambda x:x[0])
print('Letter data loaded.')



@app.route('/')
def index():
    global DATA
    findata = []
    for elem in DATA:
        findata.append({"catalogue": elem[0], "date":elem[1], "addressee": elem[2], "keywords": elem[3], "regions":elem[4]})
    return render_template('index.html', data=findata)


@app.route('/viewitem/<string:itemindex>')
def viewitem(itemindex):
    for s in os.listdir(DOCTXT_REL_DIR):
        if os.path.isfile(os.path.join(DOCTXT_REL_DIR, s)) and s.startswith(itemindex):
            return send_file(os.path.join(DOC_REL_DIR, f'{s.rsplit(".", 1)[0]}.doc'))
    return "NO FILE FOUND"


if __name__ == '__main__':
    app.run(debug=True)
