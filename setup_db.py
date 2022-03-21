#!/usr/bin/env python3


"""
SQL setup file, run once

"""


import os
import sqlite3
import config as cfg


query_table_atms = """CREATE TABLE IF NOT EXISTS atms(
            id INTEGER PRIMARY KEY,
            atm_id INTEGER,
            atm_city TEXT,
            atm_where TEXT,
            atm_address TEXT,
            latitude TEXT,
            longitude TEXT,
            atm_usd_amount INT,
            atm_eur_amount INT,
            atm_rub_amount INT,
            atm_tcs_link TEXT,
            atm_gmaps_link TEXT,
            atm_ymaps_link TEXT);
        """


db = os.path.join(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))), cfg.DB_NAME)
if os.path.isfile(db):
    print("Database already exists, rename or remove and re-run this script.")
else:
    conn = sqlite3.connect(db, check_same_thread=False)
    cur = conn.cursor()
    cur.execute(query_table_atms)
    print("Database successfully created.")
    conn.commit()
    conn.close()
    print("Finished.")
