DB_NAME = "atms.db"

CITY = "Нижний Новгород"

# Nizhniy Novgorod
NN_QUERY_BOTTOM_LEFT_LAT = 56.16316146809885
NN_QUERY_BOTTOM_LEFT_LNG = 43.98961897456331
NN_QUERY_TOP_RIGHT_LAT = 56.366949621954355
NN_QUERY_TOP_RIGHT_LNG = 44.288261284887945
NN_QUERY_ZOOM = 9

CURRENCY_FILTERS_AMOUNT = {"USD": 0}

CASH_MONITOR_SKIP_ATMS_IDS = "{'000000'}"  # ATM's ids which should be excluded from monitoring

API_URL = 'https://api.tinkoff.ru/geo/withdraw/clusters'

POLL_DELAY_SECONDS = 30  # Do not set it too low, may result in temporary ban from API
