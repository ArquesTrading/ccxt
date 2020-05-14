# -*- coding: utf-8 -*-

import os
import sys
import hmac
import base64
import requests
import json
import time
import ccxt
import telepot
import matplotlib.pyplot as plt
import seaborn
import numpy as np
from scipy.stats import norm

# root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# sys.path.append(root + '/python')

root = os.path.dirname(os.path.abspath(__file__))

unit = 100              # in US Dollar
threshold = 0.002       # 0.0n refers to n%

bitmex = ccxt.bitmex()
bitmex.apiKey = 'cnwuv67boFbZ6EXfcakUzP'
bitmex.secret = 'utqh8NNRy0LvnXW5UEmwZtDtzR8unl5T0ug48cCUqaB5nJ'
bitstamp = ccxt.bitstamp()
bitstamp.apiKey = 'rPYYjKCVvpb1NVt6tB4HbxE9TJduB9'
bitstamp.secret = '3ImJUPIq2D8Cze120y4M5GE8MxoXo9'
bitstamp.uid = '794730'


# Authentication

bitstamp.check_required_credentials()
bitmex.check_required_credentials()


while True:

    # Orderbook

    orderbook_bitmex = bitmex.fetch_order_book(symbol='BTC/USD')

    print(orderbook_bitmex['bids'])
    print(orderbook_bitmex['asks'])

    orderbook_bitstamp = bitstamp.fetch_order_book(symbol='BTC/USD')

    print(orderbook_bitstamp['bids'])
    print(orderbook_bitstamp['asks'])

    unit_satoshi = round(unit/orderbook_bitstamp['bids'][0][0], 8)


    # Target Price

    bitmex_bids_sum = 0
    bitmex_asks_sum = 0
    bitstamp_bids_sum = 0
    bitstamp_asks_sum = 0

    for i in range(10):
        bitmex_bids_sum += orderbook_bitmex['bids'][i][1]
        if bitmex_bids_sum > unit:
            bitmex_bids_no = i
            break

    for i in range(10):
        bitmex_asks_sum += orderbook_bitmex['asks'][i][1]
        if bitmex_asks_sum > unit:
            bitmex_asks_no = i
            break

    for i in range(10):
        bitstamp_bids_sum += orderbook_bitstamp['bids'][i][1]
        if bitstamp_bids_sum > unit_satoshi:
            bitstamp_bids_no = i
            break

    for i in range(10):
        bitstamp_asks_sum += orderbook_bitstamp['asks'][i][1]
        if bitstamp_asks_sum > unit_satoshi:
            bitstamp_asks_no = i
            break

    print(bitmex_bids_no, bitmex_asks_no, bitstamp_bids_no, bitstamp_asks_no)


    # Create Orders

    index = 0       # 0: No position / 1: Bitmex short position / 2: Bitmex long position
    ratio1 = round(orderbook_bitmex['bids'][bitmex_bids_no][0] / orderbook_bitstamp['asks'][bitstamp_asks_no][0], 8)
    ratio2 = round(orderbook_bitstamp['bids'][bitstamp_bids_no][0] / orderbook_bitmex['asks'][bitmex_asks_no][0], 8)

    if index == 0:
        if ratio1 > 1 + threshold:
            # Bitmex open short / Bitstamp buy
            if bitstamp.fetch_balance['info']['usd_available'] > unit * 2:
                bitmex.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit, price=None)
                bitstamp.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit_satoshi, price=None)
                # if bitmex position == short → index = 1
                # if bitmex position == long → index = 2
                # if bitmex porition == none → index = 0
            else:
                pass
        elif ratio2 > 1 + threshold:
            # Bitmex open long / Bitstamp sell
            if bitstamp.fetch_balance['info']['btc_available'] > unit_satoshi * 2:
                bitstamp.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit_satoshi, price=None)
                bitmex.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit, price=None)
                # if bitmex position == short → index = 1
                # if bitmex position == long → index = 2
                # if bitmex porition == none → index = 0
            else:
                pass
        else:
            pass
    elif index == 1:
        if ratio1 > 1 + threshold:
            # Bitmex open short / Bitstamp buy
            if bitstamp.fetch_balance['info']['usd_available'] > unit * 2:
                bitmex.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit, price=None)
                bitstamp.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit_satoshi, price=None)
                # if bitmex position == short → index = 1
                # if bitmex position == long → index = 2
                # if bitmex porition == none → index = 0
            else:
                pass
        elif ratio1 < 1:
            # Bitmex close short / Bitstamp sell
            if bitstamp.fetch_balance['info']['btc_available'] > unit_satoshi * 2:
                bitmex.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit, price=None)
                bitstamp.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit_satoshi, price=None)
                # if bitmex position == short → index = 1
                # if bitmex position == long → index = 2
                # if bitmex porition == none → index = 0
            else:
                pass
        else:
            pass
    elif index == 2:
        if ratio2 > 1 + threshold:
            # Bitmex open long / Bitstamp sell
            if bitstamp.fetch_balance['info']['btc_available'] > unit_satoshi * 2:
                bitmex.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit, price=None)
                bitstamp.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit_satoshi, price=None)
                # if bitmex position == short → index = 1
                # if bitmex position == long → index = 2
                # if bitmex porition == none → index = 0
            else:
                pass
        elif ratio2 < 1:
            # Bitmex close long / Bitstamp buy
            if bitstamp.fetch_balance['info']['usd_available'] > unit * 2:
                bitmex.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit, price=None)
                bitstamp.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit_satoshi, price=None)
                # if bitmex position == short → index = 1
                # if bitmex position == long → index = 2
                # if bitmex porition == none → index = 0
            else:
                pass
        else:
            pass
    else:
        pass

    time.sleep(1)
