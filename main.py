from flask import (
    Flask,
    render_template,
    send_file,
    redirect,
    request,
    url_for,
)
import os
import sqlite3
import re

# Login management imports
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests


# Internal imports
from db import init_db_command
from user import User
from app_helper import (
    DOC_TXT_REL_DIR,
    DOC_REL_DIR,
    TEXT_INPUT_FIELDS,
    CHECKBOX_INPUT_FIELDS,
    CLIENT_SECRET,
    CLIENT_ID,
    unload_data,
    filter_data,
    close_conn,
)  # load constants and functions


app = Flask(__name__)



# LOAD DATA AT START
DATADICT = unload_data()
close_conn()


@app.route('/')
def index():
    """The main page of the website."""
    return redirect(url_for('search'))


@app.route('/viewitem/<string:itemindex>')
def viewitem(itemindex):
    """The page of a specific letter."""
    for s in os.listdir(DOC_TXT_REL_DIR):
        if os.path.isfile(os.path.join(DOC_TXT_REL_DIR, s)) and s.startswith(itemindex):
            return send_file(os.path.join(DOC_REL_DIR, f'{s.rsplit(".", 1)[0]}.doc'))
    return 'NO FILE FOUND'


@app.route('/search', methods=['POST', 'GET'])
def search():
    """Return the search values."""
    if request.method == 'POST':
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
        return render_template('search.html', data=filter_data(DATADICT, textfields, sorting_params=checkbox_items_on))
    else:
        return render_template('search.html', data=DATADICT)


if __name__ == '__main__':
    app.run(debug=True)
