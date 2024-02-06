import os
import sqlite3
import time
import urllib.request

from typing import NamedTuple

import requests

import config

BASE_URL_TCS = "https://www.tinkoff.ru/maps/atm/?latitude={lat}&longitude={long}&zoom=20"
BASE_URL_GMAPS = "https://www.google.com/maps/search/?api=1&query={lat}%2C{long}"
BASE_URL_YMAPS = "https://yandex.ru/maps/?mode=search&text={lat}%2C+{long}"
BASE_TINKOFF_API = "https://api.tinkoff.ru/geo/withdraw/clusters"

query_table_atms = """CREATE TABLE IF NOT EXISTS atms(
            id INTEGER PRIMARY KEY,
            atm_id INTEGER,
            city TEXT,
            place TEXT,
            address TEXT,
            latitude TEXT,
            longitude TEXT,
            usd_amount INT,
            tcs_link TEXT,
            gmaps_link TEXT,
            ymaps_link TEXT);
        """

db = os.path.join(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))), config.DB_NAME)
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

# Initialization
db = os.path.join(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))), config.DB_NAME)
conn = sqlite3.connect(db, check_same_thread=False)
cur = conn.cursor()


class AvailableCash(NamedTuple):
    currency: str
    amount: int


class ATM(NamedTuple):
    id: str
    location: str
    lat: float
    long: float
    available_cash: list[AvailableCash]


def get_atms_info(city) -> list[dict]:
    if city == "Нижний Новгород":
        curr_city_bottom_left_lat = config.NN_QUERY_BOTTOM_LEFT_LAT
        curr_city_bottom_left_long = config.NN_QUERY_BOTTOM_LEFT_LNG
        curr_city_top_right_lat = config.NN_QUERY_TOP_RIGHT_LAT
        curr_city_top_right_long = config.NN_QUERY_TOP_RIGHT_LNG
        curr_city_zoom = config.NN_QUERY_ZOOM
    else:
        print("В конфиге нет данных для города", city)
        return []
    result = {}
    for currency in config.CURRENCY_FILTERS_AMOUNT:
        response = requests.post(
            url=config.API_URL,
            json={
                'bounds': {
                    'bottomLeft': {'lat': curr_city_bottom_left_lat, 'lng': curr_city_bottom_left_long},
                    'topRight': {'lat': curr_city_top_right_lat, 'lng': curr_city_top_right_long},
                },
                'filters': {
                    'showUnavailable': False,
                    'currencies': [currency],
                },
                'zoom': curr_city_zoom,
            },
        )
        assert response.status_code == 200, (response.status_code, response.text)
        response = response.json()
        for cluster in response['payload']['clusters']:
            for atm_info in cluster['points']:
                result[atm_info['id']] = atm_info
    return list(result.values())


def get_suitable_atms(city) -> list[ATM]:
    result = []
    atms_info = get_atms_info(city)
    for atm_info in atms_info:
        if (
                (atm_id := atm_info['id']) in config.CASH_MONITOR_SKIP_ATMS_IDS
                or atm_info['pointType'] != 'ATM'
                or atm_info['brand']['name'].lower() != 'тинькофф банк'
        ):
            continue

        curr_amounts = {
            curr_name: AvailableCash(
                currency=curr_name,
                amount=limit['amount'],
            )
            for limit in atm_info['limits']
            if (curr_name := limit['currency']) in config.CURRENCY_FILTERS_AMOUNT
        }

        if any(
                (avail_curr := curr_amounts.get(curr_name)) and avail_curr.amount >= expected_amount
                for curr_name, expected_amount in config.CURRENCY_FILTERS_AMOUNT.items()
        ):
            location = atm_info['location']
            result.append(ATM(
                id=atm_id,
                location=atm_info['address'],
                lat=location['lat'],
                long=location['lng'],
                available_cash=list(curr_amounts.values()),
            ))

    return result


def save_report(atms: list, city: str):
    for atm in atms:
        amount = 0
        for currency in atm.available_cash:
            if currency.currency == "USD":
                amount = currency.amount
        usd_amount = amount
        items_list = atm.location.split(",")
        index_count = len(items_list)
        address = str(items_list[index_count - 2]) + str(items_list[index_count - 1])
        where = atm.location[:-(len(address) + 2)]
        result1 = where, address
        place, address = result1
        result = BASE_URL_TCS.format(lat=atm.lat, long=atm.long), BASE_URL_GMAPS.format(lat=atm.lat,
                                                                                        long=atm.long), BASE_URL_YMAPS.format(
            lat=atm.lat, long=atm.long)
        tcs_link, gmaps_link, ymaps_link = result
        cur.execute(f"SELECT * FROM atms WHERE atm_id = '{atm.id}'")
        if not len(cur.fetchall()) > 0:
            query = "INSERT INTO atms VALUES (null, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            cur.execute(query, (
                atm.id, city, place, address, atm.lat, atm.long, usd_amount, tcs_link, gmaps_link,
                ymaps_link))
        else:
            cur.execute(f"UPDATE atms SET usd_amount = '{usd_amount}' WHERE atm_id = '{atm.id}'")
            conn.commit()


def try_find_cash():
    is_api_ok = urllib.request.urlopen(BASE_TINKOFF_API).getcode() == 200

    if not is_api_ok:
        print("API is unreachable")
        return

    city = config.CITY
    suitable_atms = get_suitable_atms(city)
    if suitable_atms:
        save_report(suitable_atms, city)


def main():
    while True:
        try:
            try:
                print("Polling ATMs")
                try_find_cash()
            except Exception as e:
                print(e)
            time.sleep(config.POLL_DELAY_SECONDS)
        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    main()
