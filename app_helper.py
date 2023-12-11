from os import environ
import sqlite3
import glob
import re
from dotenv import load_dotenv
import requests
import json

load_dotenv()  # load secret keys

DB_FILE = 'maindb.db'
DOC_TXT_REL_DIR = 'documents-txt'
DOC_REL_DIR = 'documents'

TEXT_INPUT_FIELDS = ['catalogue', 'date', 'addressee', 'keywords', 'regions']
CHECKBOX_INPUT_FIELDS = ['case-sensitive', 'use-regex', 'replace-e', 'published']
DATA_FIELDS = ['catalogue', 'date', 'addressee', 'keywords', 'regions',
               'contents_txt', 'filename', 'imagelink', 'published']

GOOGLE_CLIENT_SECRET = environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_CLIENT_ID = environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

APPROVED_EMAILS = json.loads(environ.get("APPROVED_EMAILS", None))

con = sqlite3.connect(DB_FILE, check_same_thread=False)
cur = con.cursor()
print('Dependencies loaded.')


def get_google_provider_cfg():
    """Return the google provider config in a json format."""
    return requests.get(GOOGLE_DISCOVERY_URL).json()


def unload_data():
    """Unload the data from DB_FILE to variable DATADICT."""
    global con, cur
    con.row_factory = sqlite3.Row
    cur.execute('SELECT * FROM letterdb')
    # Data processing
    DATA = cur.fetchall()
    DATA.sort(key=lambda x: x[0])
    DATADICT = []
    for elem in DATA:
        DATADICT.append(dict(zip(DATA_FIELDS, elem)))
    print('Letter data loaded.')
    return DATADICT


def filter_data(data, filter_dict, sorting_params=[]):
    """Filter the data to return the values for /search."""
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
            if key == 'contents':
                matchout = re.match(value, finkey, flags=re.DOTALL)
            elif key == 'contents' and 'case-sensitive' in sorting_params:
                matchout = re.match(value, finkey, flags=re.IGNORECASE | re.DOTALL)
            else:
                matchout = re.match(value, finkey)
            if value != '' and not matchout:
                match = False
                break
        if match:
            filtered_data.append(d)
    return filtered_data


def create_table(force=False):
    """Create a table."""
    global cur, con
    if force:
        cur.execute("DROP TABLE IF EXISTS letterdb")
    cur.execute("""CREATE TABLE IF NOT EXISTS letterdb (
                catalogue,
                date,
                adressee,
                keywords,
                regions,
                contents_txt,
                filename,
                imagelink,
                published DEFAULT 0
                )""")


def load_data():
    """Load the letter data into the table."""
    global cur, con
    name_pattern = r"^(\d{3})\s*Обручев\s*(.{4})\s*-\s*(.*?)\.txt$"
    print("This might take a while, depending on the size of the files.")
    for filename in glob.iglob(f'{DOC_TXT_REL_DIR}/*'):
        filename_raw = filename.rsplit("/", 1)[-1]
        filename_data = list(re.findall(name_pattern, filename_raw)[0])

        # Remove y from recepient
        assembled_recepient = []
        for s in filename_data[2].split():
            if s.endswith('у') or s.endswith('ю'):  # cyrillic letter
                assembled_recepient.append(s[:-1])
            else:
                assembled_recepient.append(s)
        filename_data[2] = ' '.join(assembled_recepient)

        with open(filename, "r") as file_data:
            file_contents = file_data.read()
        fin_values = tuple(filename_data) + (file_contents, filename_raw)
        cur.execute("INSERT INTO letterdb (catalogue, date, adressee, contents_txt, filename)"
                    "VALUES (?, ?, ?, ?, ?)", fin_values)
        con.commit()


def update_row(row, number):
    """Updates the row in the database."""
    global cur, con
    query = f"""UPDATE letterdb
SET catalogue = '{row["catalogue"]}',
date = '{row["date"]}',
adressee = '{row["addressee"]}',
keywords = '{row["keywords"]}',
regions = '{row["regions"]}',
contents_txt = '{row["contents_txt"]}',
filename = '{row["filename"]}',
imagelink = '{row["imagelink"]}',
published = '{row["published"]}'
WHERE catalogue = '{number}';"""
    cur.execute(query)
    con.commit()


def close_conn():
    """Close the connection."""
    con.close()
