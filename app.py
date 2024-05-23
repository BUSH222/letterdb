from flask import (
    Flask,
    render_template,
    redirect,
    request,
    url_for,
    abort,
)
import os
import sqlite3
import json

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
    TEXT_INPUT_FIELDS,
    CHECKBOX_INPUT_FIELDS,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_CLIENT_ID,
    APPROVED_EMAILS,
    unload_data,
    filter_data,
    get_google_provider_cfg,
    update_row,
    add_row,
    delete_row,
)

app = Flask(__name__)

# Load data at start
DATADICT = unload_data()

# Google things
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

login_manager = LoginManager()
login_manager.init_app(app)

try:
    init_db_command()
except sqlite3.OperationalError:
    pass

client = WebApplicationClient(GOOGLE_CLIENT_ID)


@login_manager.user_loader
def load_user(user_id):
    """Load the user data."""
    return User.get(user_id)


@app.route("/")
def index():
    """Index of the webpage."""
    return render_template('index.html')


@app.route("/about")
def about():
    """About page."""
    return render_template('about.html')


@app.route("/contact")
def contact():
    """Contact page."""
    return render_template('contact.html')


@app.route("/search_manual")
def search_manual():
    """Contact page."""
    return render_template('search_manual.html')


@app.route("/login")
def login():
    """Begin the login sequence"""
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    """Get authorization code Google sent back to you"""
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # 403 if user is not in approved emails
    if users_email not in APPROVED_EMAILS:
        abort(403)

    user = User(id_=unique_id, name=users_name, email=users_email, profile_pic=picture)
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    login_user(user)

    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    """Log out"""
    logout_user()
    return redirect(url_for("index"))


@app.route('/viewitem/<string:itemindex>')
def viewitem(itemindex):
    """The page of a specific letter."""
    if not itemindex.isdigit():
        abort(400)
    current_letter_data = {}

    for elem in DATADICT:
        if elem['catalogue'] == itemindex:
            current_letter_data = elem
            break

    hidden = "hidden"

    if current_user.is_authenticated and current_user.email in APPROVED_EMAILS:
        hidden = ""

    return render_template("letterview.html", data=current_letter_data, hidden=hidden)


@app.route('/newletter')
def newletter():
    """The page for creating a new letter"""
    if not current_user.is_authenticated:
        abort(403)
    if current_user.email not in APPROVED_EMAILS:
        abort(403)
    return render_template("newletter.html")


@app.route('/finalise_new_letter', methods=['POST'])
def finalise_new_letter():
    """Finalise the process of creating a new letter."""
    if not current_user.is_authenticated:
        abort(403)
    if current_user.email not in APPROVED_EMAILS:
        abort(403)
    formdata = dict(request.form)

    DATADICT.append(formdata)
    add_row(formdata.values())

    return redirect(url_for("viewitem", itemindex=formdata["catalogue"]))


@app.route('/edit/<string:itemindex>')
def edititem(itemindex):
    """Edit page of a specific letter."""
    if not current_user.is_authenticated:
        abort(403)
    if current_user.email not in APPROVED_EMAILS:
        abort(403)
    if not itemindex.isdigit():
        abort(400)
    current_letter_data = {}

    for elem in DATADICT:
        if elem['catalogue'] == itemindex:
            current_letter_data = elem
            break

    return render_template("letteredit.html", data=current_letter_data)


@app.route('/finalise_edit/<string:itemindex>', methods=['POST', 'GET'])
def finalise_edit(itemindex):
    """Finalise the editing process, save results."""
    global DATADICT
    if not current_user.is_authenticated:
        abort(403)
    if current_user.email not in APPROVED_EMAILS:
        abort(403)
    if not itemindex.isdigit():
        abort(400)
    cnt = 0
    for elem in DATADICT:
        if elem['catalogue'] == itemindex:
            if dict(request.form).keys() == elem.keys():
                DATADICT[cnt] = dict(request.form)
                break
        cnt += 1
    update_row(dict(request.form), itemindex)
    return redirect(url_for('viewitem', itemindex=itemindex))


@app.route('/delete/<string:itemindex>', methods=['GET'])
def delete_letter(itemindex):
    if not current_user.is_authenticated:
        abort(403)
    if current_user.email not in APPROVED_EMAILS:
        abort(403)
    if not itemindex.isdigit():
        abort(400)
    todel = None
    for elem in DATADICT:
        if elem['catalogue'] == itemindex:
            todel = elem
            break
    DATADICT.remove(todel)
    delete_row(itemindex)
    return redirect(url_for('search'))


@app.route('/search', methods=['POST', 'GET'])
def search():
    """Return the search values."""
    hidden = 'hidden'
    if request.method == 'POST':
        query = dict(request.form)
        textfields = {}
        checkbox_items_on = []
        for s in query.items():
            if s[0] in TEXT_INPUT_FIELDS:
                textfields[s[0]] = s[1]
            elif s[0] in CHECKBOX_INPUT_FIELDS and s[1] == 'on':
                checkbox_items_on.append(s[0])
        tempdata = filter_data(DATADICT, textfields, sorting_params=checkbox_items_on)
        if len(tempdata) != 0:
            return render_template('search.html', data=tempdata, notfoundhidden=hidden)
        else:
            return render_template('search.html', data=tempdata, notfoundhidden='')

    else:
        return render_template('search.html', data=DATADICT, notfoundhidden=hidden)


if __name__ == '__main__':
    app.run(ssl_context="adhoc")
