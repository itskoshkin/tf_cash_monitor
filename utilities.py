"""
Utilities file

"""

import os
import sqlite3
import config as cfg


# Initialization
db = os.path.join(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))), cfg.DB_NAME)
conn = sqlite3.connect(db, check_same_thread=False)
cur = conn.cursor()


# Main function to call from tacm.py
def save_atm_info(atm_id, atm_city, atm_location, atm_lat, atm_long, atm_usd_amount, atm_eur_amount, atm_rub_amount):
    items_list = atm_location.split(",")
    index_count = len(items_list)
    atm_where = atm_location
    atm_address = str(items_list[index_count - 2]) + str(items_list[index_count - 1])
    atm_where = atm_where[:-(len(atm_address)+2)]
    # https://www.tinkoff.ru/maps/atm/?latitude=56.309291&longitude=43.988014&zoom=20
    atm_tcs_link = "https://www.tinkoff.ru/maps/atm/?latitude=" + str(atm_lat) + "&longitude=" + str(atm_long) + "&zoom=20"
    # https://www.google.com/maps/search/?api=1&query=56.3092918%2C43.988014
    atm_gmaps_link = "https://www.google.com/maps/search/?api=1&query=" + str(atm_lat) + "%2C" + str(atm_long)
    # https://yandex.ru/maps/?mode=search&text=56.309291%2C+43.988014
    atm_ymaps_link = "https://yandex.ru/maps/?mode=search&text=" + str(atm_lat) + "%2C+" + str(atm_long)
    if not check_if_atm_present(atm_id):
        pass
        save_new_atm(atm_id, atm_city, atm_where, atm_address, atm_lat, atm_long, atm_usd_amount, atm_eur_amount, atm_rub_amount, atm_tcs_link, atm_gmaps_link, atm_ymaps_link)
    else:
        edit_atm_currency(atm_id, atm_usd_amount, atm_eur_amount, atm_rub_amount)


# Check if ATM already exist in database
def check_if_atm_present(atm_id):
    cur.execute("SELECT * FROM atms WHERE atm_id = '{}'".format(atm_id))
    result = cur.fetchall()
    if len(result) > 0:
        return True
    else:
        return False


# Save new ATM
def save_new_atm(atm_id, atm_city, atm_where, atm_address, latitude, longitude, atm_usd_amount, atm_eur_amount, atm_rub_amount, atm_tcs_link, atm_gmaps_link, atm_ymaps_link):
    query = "INSERT INTO atms VALUES (null, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    cur.execute(query, (atm_id, atm_city, atm_where, atm_address, latitude, longitude, atm_usd_amount, atm_eur_amount, atm_rub_amount, atm_tcs_link, atm_gmaps_link, atm_ymaps_link))


# If ATN exists, just update it's contents
def edit_atm_currency(atm_id, usd_amount, eur_amount, rub_amount):
    cur.execute("UPDATE atms SET atm_usd_amount = '{}', atm_eur_amount = '{}', atm_rub_amount = '{}' WHERE atm_id = '{}'".format(usd_amount, eur_amount, rub_amount, atm_id))
    conn.commit()
