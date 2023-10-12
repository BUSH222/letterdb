import sqlite3


con = sqlite3.connect("maindb.db")
cur = con.cursor()


def create_table():
    """Create a table."""
    global cur, con
    cur.execute("CREATE TABLE IF NOT EXISTS letterdb(catalogue, date, adressee, keywords, regions)")


def load_data():
    """Load the letter data into the table."""
    global cur, con
    pass  # TODO: VERIFY that the numbers of files match the table values


create_table()
con.close()
