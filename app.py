import os

from flask import (
    Flask,
    abort,
    redirect,
    render_template,
    request,
    url_for,
)

# Login management imports
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from app_helper import (
    CHECKBOX_INPUT_FIELDS,
    TEXT_INPUT_FIELDS,
    add_row,
    delete_row,
    filter_data,
    unload_data,
    update_row,
)

# Internal imports
from user import User

app = Flask(__name__)

# Load data at start
DATADICT = unload_data()

# Login management
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    """Load the user data."""
    return User.get(user_id)


@app.route("/")
def index():
    """Index of the webpage."""
    return render_template("index.html")


@app.route("/about")
def about():
    """About page."""
    return render_template("about.html")


@app.route("/contact")
def contact():
    """Contact page."""
    return render_template("contact.html")


@app.route("/search_manual")
def search_manual():
    """Contact page."""
    return render_template("search_manual.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log in with an email and a password."""
    if request.method == "GET":
        return render_template("login.html", error=None)
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    user = User.authenticate(email, password)
    if user is None:
        return render_template("login.html", error="Неверный email или пароль."), 401
    login_user(user)
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    """Log out"""
    logout_user()
    return redirect(url_for("index"))


@app.route("/viewitem/<string:itemindex>")
def viewitem(itemindex):
    """The page of a specific letter."""
    if not itemindex.isdigit():
        abort(400)
    current_letter_data = {}

    for elem in DATADICT:
        if elem["catalogue"] == itemindex:
            current_letter_data = elem
            break

    hidden = "hidden"

    if current_user.is_authenticated:
        hidden = ""
    print(current_letter_data)
    return render_template("letterview.html", data=current_letter_data, hidden=hidden)


@app.route("/newletter")
def newletter():
    """The page for creating a new letter"""
    if not current_user.is_authenticated:
        abort(403)
    return render_template("newletter.html")


@app.route("/finalise_new_letter", methods=["POST"])
def finalise_new_letter():
    """Finalise the process of creating a new letter."""
    if not current_user.is_authenticated:
        abort(403)
    formdata = dict(request.form)

    DATADICT.append(formdata)
    add_row(formdata.values())

    return redirect(url_for("viewitem", itemindex=formdata["catalogue"]))


@app.route("/edit/<string:itemindex>")
def edititem(itemindex):
    """Edit page of a specific letter."""
    if not current_user.is_authenticated:
        abort(403)
    if not itemindex.isdigit():
        abort(400)
    current_letter_data = {}

    for elem in DATADICT:
        if elem["catalogue"] == itemindex:
            current_letter_data = elem
            break

    return render_template("letteredit.html", data=current_letter_data)


@app.route("/finalise_edit/<string:itemindex>", methods=["POST", "GET"])
def finalise_edit(itemindex):
    """Finalise the editing process, save results."""
    global DATADICT
    if not current_user.is_authenticated:
        abort(403)
    if not itemindex.isdigit():
        abort(400)
    for cnt, elem in enumerate(DATADICT):
        if elem["catalogue"] == itemindex and dict(request.form).keys() == elem.keys():
            DATADICT[cnt] = dict(request.form)
            break
    update_row(dict(request.form), itemindex)
    return redirect(url_for("viewitem", itemindex=itemindex))


@app.route("/delete/<string:itemindex>", methods=["GET"])
def delete_letter(itemindex):
    if not current_user.is_authenticated:
        abort(403)
    if not itemindex.isdigit():
        abort(400)
    todel = None
    for elem in DATADICT:
        if elem["catalogue"] == itemindex:
            todel = elem
            break
    DATADICT.remove(todel)
    delete_row(itemindex)
    return redirect(url_for("search"))


@app.route("/search", methods=["POST", "GET"])
def search():
    """Return the search values."""
    hidden = "hidden"
    if request.method == "POST":
        query = dict(request.form)
        textfields = {}
        checkbox_items_on = []
        for s in query.items():
            if s[0] in TEXT_INPUT_FIELDS:
                textfields[s[0]] = s[1]
            elif s[0] in CHECKBOX_INPUT_FIELDS and s[1] == "on":
                checkbox_items_on.append(s[0])
        tempdata = filter_data(DATADICT, textfields, sorting_params=checkbox_items_on)
        if len(tempdata) != 0:
            return render_template("search.html", data=tempdata, notfoundhidden=hidden)
        else:
            return render_template("search.html", data=tempdata, notfoundhidden="")

    else:
        return render_template("search.html", data=DATADICT, notfoundhidden=hidden)


if __name__ == "__main__":
    app.run(ssl_context="adhoc")
