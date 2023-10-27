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
cur.execute('SELECT * FROM letterdb')

TEXT_INPUT_FIELDS = ['catalogue', 'date', 'addressee', 'keywords', 'regions']
CHECKBOX_INPUT_FIELDS = ['case-sensitive', 'use-regex', 'replace-e', 'published']

# Data processing
DATA = cur.fetchall()
DATA.sort(key=lambda x: x[0])
DATADICT = []
for elem in DATA:
    DATADICT.append(dict(zip(TEXT_INPUT_FIELDS, elem)))
DATADICT.append(dict(zip(TEXT_INPUT_FIELDS, ["999", '2000', "Агранёнок", "None", "None"])))

print('Letter data loaded.')


def filter_data(data, filter_dict, sorting_params=[]):
    """Filter the data to return the values for /search."""
    # assert all([m in sorting_params for m in CHECKBOX_INPUT_FIELDS]) or len(sorting_params) == 0
    filtered_data = []

    if 'published' in sorting_params:
        pass  # TODO
    for d in data:
        match = True
        for key, value in filter_dict.items():
            finkey = str(d.get(key))
            if 'use-regex' not in sorting_params:
                value = value.replace('*', '.*')
            if 'replace-e' in sorting_params:
                value = value.replace('ё', 'е')  # cyrillic
                finkey = str(d.get(key)).replace('ё', 'е')
            if 'case-sensitive' in sorting_params:
                matchout = re.match(value, finkey, flags=re.IGNORECASE)
            else:
                matchout = re.match(value, finkey)
            if value != '' and not matchout:
                match = False
                break
        if match:
            filtered_data.append(d)
    return filtered_data


@app.route('/')
def index():
    """The main page of the website."""
    return render_template('index.html', data=DATADICT)


@app.route('/viewitem/<string:itemindex>')
def viewitem(itemindex):
    """The page of a specific letter."""
    for s in os.listdir(DOCTXT_REL_DIR):
        if os.path.isfile(os.path.join(DOCTXT_REL_DIR, s)) and s.startswith(itemindex):
            return send_file(os.path.join(DOC_REL_DIR, f'{s.rsplit(".", 1)[0]}.doc'))
    return 'NO FILE FOUND'


@app.route('/search', methods=['POST'])
def search():
    """Return the search values."""
    query = dict(request.form)
    print(query)
    textfields = {}
    checkbox_items_on = []

    for s in query.items():
        if s[0] in TEXT_INPUT_FIELDS:
            textfields[s[0]] = s[1]
        elif s[0] in CHECKBOX_INPUT_FIELDS and s[1] == 'on':
            checkbox_items_on.append(s[0])

    print(textfields)
    print(checkbox_items_on)
    return render_template('index.html', data=filter_data(DATADICT, textfields, sorting_params=checkbox_items_on))


if __name__ == '__main__':
    app.run(debug=True)
