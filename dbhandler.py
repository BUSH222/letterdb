import sqlite3
import glob
import re

DOC_REL_DIR = 'documents'
DOC_TXT_REL_DIR = 'documents-txt'
con = sqlite3.connect("maindb.db")
cur = con.cursor()


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


# create_table(force=True)
# load_data()

con.close()
