from os import environ
import sqlite3
import glob
import re
from dotenv import load_dotenv

load_dotenv()  # load secret keys

DB_FILE = 'maindb.db'
DOC_TXT_REL_DIR = 'documents-txt'
DOC_REL_DIR = 'documents'

TEXT_INPUT_FIELDS = ['catalogue', 'date', 'addressee', 'keywords', 'regions']
CHECKBOX_INPUT_FIELDS = ['case-sensitive', 'use-regex', 'replace-e', 'published']

CLIENT_SECRET = environ["GOOGLE_CLIENT_SECRET"]
CLIENT_ID = environ["GOOGLE_CLIENT_ID"]

con = sqlite3.connect(DB_FILE)
cur = con.cursor()
print('Dependencies loaded.')


def unload_data():
    global con, cur
    """Unload the data from DB_FILE to variable DATADICT"""
    con.row_factory = sqlite3.Row
    cur.execute('SELECT * FROM letterdb')
    # Data processing
    DATA = cur.fetchall()
    DATA.sort(key=lambda x: x[0])
    DATADICT = []
    for elem in DATA:
        DATADICT.append(dict(zip(TEXT_INPUT_FIELDS, elem)))
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
    cur.execute("CREATE TABLE IF NOT EXISTS letterdb(catalogue, date, adressee, keywords, regions, contents_txt, filename)")


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


def close_conn():
    """Close the connection."""
    con.close()
