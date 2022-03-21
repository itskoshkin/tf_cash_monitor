#!/usr/bin/python3.9


"""
Main file

Forked from https://github.com/frosthamster/tf_cash_monitor/
"""


import time
import requests
import urllib.request
from typing import NamedTuple
import utilities as utils
import config


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
        # print("Найдены данные для ", city)
        curr_city_bottom_left_lat = config.NN_QUERY_BOTTOM_LEFT_LAT
        curr_city_bottom_left_long = config.NN_QUERY_BOTTOM_LEFT_LNG
        curr_city_top_right_lat = config.NN_QUERY_TOP_RIGHT_LAT
        curr_city_top_right_long = config.NN_QUERY_TOP_RIGHT_LNG
        curr_city_zoom = config.NN_QUERY_ZOOM
    elif city == "Санкт-Петербург":
        # print("Найдены данные для ", city)
        curr_city_bottom_left_lat = config.SPB_QUERY_BOTTOM_LEFT_LAT
        curr_city_bottom_left_long = config.SPB_QUERY_BOTTOM_LEFT_LNG
        curr_city_top_right_lat = config.SPB_QUERY_TOP_RIGHT_LAT
        curr_city_top_right_long = config.SPB_QUERY_TOP_RIGHT_LNG
        curr_city_zoom = config.SPB_QUERY_ZOOM
    elif city == "Москва и МО":
        # print("Найдены данные для ", city)
        curr_city_bottom_left_lat = config.MSK_QUERY_BOTTOM_LEFT_LAT
        curr_city_bottom_left_long = config.MSK_QUERY_BOTTOM_LEFT_LNG
        curr_city_top_right_lat = config.MSK_QUERY_TOP_RIGHT_LAT
        curr_city_top_right_long = config.MSK_QUERY_TOP_RIGHT_LNG
        curr_city_zoom = config.MSK_QUERY_ZOOM
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
                    'showUnavailable': True,
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


# def save_report(atms: list[ATM], city) -> str:
def save_report(atms: list[ATM], city):
    for atm in atms:
        usd_amount = 0
        eur_amount = 0
        rub_amount = 0
        for currency in atm.available_cash:
            if currency.currency == "USD":
                usd_amount = currency.amount
            if currency.currency == "EUR":
                eur_amount = currency.amount
            if currency.currency == "RUB":
                rub_amount = currency.amount
        utils.save_atm_info(atm.id, city, atm.location, atm.lat, atm.long, usd_amount, eur_amount, rub_amount)


def try_find_cash():
    print("Checking status")
    if urllib.request.urlopen("https://api.tinkoff.ru/geo/withdraw/clusters").getcode() == 200:
        print("Status OK:", urllib.request.urlopen("https://api.tinkoff.ru/geo/withdraw/clusters").getcode())
    else:
        print("Status:", urllib.request.urlopen("https://api.tinkoff.ru/geo/withdraw/clusters").getcode(), "!")
    print("\33[33mПоиск банкоматов...\x1b[0m")
    for city in config.CITIES:
        suitable_atms = get_suitable_atms(city)
        if not suitable_atms:
            print("\33[31mНе найдено\x1b[0m в банкоматов", city)
        else:
            print("\33[32mЕсть результаты\x1b[0m для", city, "-", len(suitable_atms))
            save_report(suitable_atms, city)


def main():
    while True:
        try:
            try:
                try_find_cash()
            except Exception as e:
                print(e)
            time.sleep(config.POLL_DELAY_SECONDS)
        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    main()
