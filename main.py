from flask import Flask, render_template, send_file
import os
from pathlib import Path

app = Flask(__name__)
DB_REL_DIR = 'db'
DOCTXT_REL_DIR = 'documents-txt'
DOC_REL_DIR = 'documents'


@app.route('/')
def index():
    # TEMPORARY DATA
    data = [
        {"catalogue": "000", "date":"Unknwn", "adressee": "Мартьянов", "keywords": "", "regions":""},
        {"catalogue": "001", "date":"Unknwn", "adressee": "Грав", "keywords": "", "regions":""}, 
        {"catalogue": "002", "date":"1952", "adressee": "Ларищев", "keywords": "", "regions":""}, 
        {"catalogue": "003", "date":"Unknwn", "adressee": "Смирнов", "keywords": "", "regions":""}, 
        {"catalogue": "004", "date":"1955", "adressee": "Сергей Васильевич", "keywords": "", "regions":""}, 

    ]
    return render_template('index.html', data=data)



@app.route('/viewitem/<string:itemindex>')
def viewitem(itemindex):
    for s in os.listdir(DOCTXT_REL_DIR):
        if os.path.isfile(os.path.join(DOCTXT_REL_DIR,s)) and s.startswith(itemindex):
            return send_file(os.path.join(DOC_REL_DIR,f'{s.rsplit(".", 1)[0]}.doc'))
    return "NO FILE FOUND"

if __name__ == '__main__':
    app.run(debug=True)