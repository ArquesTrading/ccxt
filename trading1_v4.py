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

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root + '/python')

unit = 100              # 테이커 주문 당 계약(달러) 수
amount = 1000           # 메이커 주문 당 계약(달러) 수 (최소한 100의 배수로)
orders = 4              # 메이커 주문 시 (위, 아래 각각) 기준가에서 멀어지면서 1000, 2000, 3000, 4000 계약단위로 주문
                        # (예) 매도 기준가가 9000달러일 경우, 9000달러 1000계약, 9000.5달러 2000계약, 9001달러 3000계약, 9001.5달러 4000계약 매도 주문
threshold1 = 0.001      # 메이킹 스프레드 0.1%
threshold2 = 0.002      # 테이킹 스프레드 0.2%
total_usd = 30000       # 시작시 달러 보유량


bitmex = ccxt.bitmex()
bitmex.apiKey = '7WBHaVBeQy70QrhsSTxuQZyd'
bitmex.secret = '8U1GCOuDxK2iG1udNWzaFtVXs7ZSbOQcGg6Tvmd0F_KSlIqG'
bitstamp = ccxt.bitstamp()
bitstamp.apiKey = 'rPYYjKCVvpb1NVt4x6tB4HbxE9TJduB9'
bitstamp.secret = '3ImJUPIq2D8Cfqze120y4M5GE8MxoXo9'
bitstamp.uid = '794730'


# Authentication

bitstamp.check_required_credentials()
bitmex.check_required_credentials()


while True:

    for i in range(30):

        # Orderbook (Orderbook은 처음에 한번 공통으로 불러오기)

        orderbook_bitstamp = bitstamp.fetch_order_book(symbol='BTC/USD')
        orderbook_bitmex = bitmex.fetch_order_book(symbol='BTC/USD')
        bitmex_best_bids = orderbook_bitmex['bids'][0][0]
        bitmex_best_asks = orderbook_bitmex['asks'][0][0]

        amount_btc = round(amount / (orderbook_bitstamp['bids'][0][0]+orderbook_bitstamp['asks'][0][0]) * 2, 8)     # 주문 당 비트코인 갯수로 환산
        unit_btc = round(unit / (orderbook_bitstamp['bids'][0][0]+orderbook_bitstamp['asks'][0][0]) * 2, 8)         # 주문 당 비트코인 갯수로 환산


        ############################## Taking Scenario ##############################


        # Best price for taking

        bitmex_bids_sum = 0
        bitmex_asks_sum = 0
        bitstamp_bids_sum = 0
        bitstamp_asks_sum = 0
        taking = 0

        for i in range(10):
            bitmex_bids_sum += orderbook_bitmex['bids'][i][1]
            if bitmex_bids_sum > unit:
                bitmex_instant_bids = orderbook_bitmex['bids'][i][0]
                break

        for i in range(10):
            bitmex_asks_sum += orderbook_bitmex['asks'][i][1]
            if bitmex_asks_sum > unit:
                bitmex_instant_asks = orderbook_bitmex['asks'][i][0]
                break

        for i in range(10):
            bitstamp_bids_sum += orderbook_bitstamp['bids'][i][1]
            if bitstamp_bids_sum > unit_btc:
                bitstamp_instant_bids = orderbook_bitstamp['bids'][i][0]
                break

        for i in range(10):
            bitstamp_asks_sum += orderbook_bitstamp['asks'][i][1]
            if bitstamp_asks_sum > unit_btc:
                bitstamp_instant_asks = orderbook_bitstamp['asks'][i][0]
                break


        # Create taking orders

        index = 0       # 0: No position / 1: Bitmex short position / 2: Bitmex long position
        ratio1 = round(bitmex_instant_bids / bitstamp_instant_asks, 8)
        ratio2 = round(bitstamp_instant_bids / bitmex_instant_asks, 8)

        if index == 0:
            if ratio1 > 1 + threshold2:
                # Bitmex open short / Bitstamp buy
                if bitstamp.fetch_balance['info']['usd_available'] > unit * 2:
                    bitmex.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit, price=None)
                    bitstamp.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit_btc, price=None)
                    # if bitmex position == short → index = 1
                    # if bitmex position == long → index = 2
                    # if bitmex porition == none → index = 0
                    taking = 1
                else:
                    taking = 0
            elif ratio2 > 1 + threshold2:
                # Bitmex open long / Bitstamp sell
                if bitstamp.fetch_balance['info']['btc_available'] > unit_btc * 2:
                    bitstamp.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit_btc, price=None)
                    bitmex.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit, price=None)
                    # if bitmex position == short → index = 1
                    # if bitmex position == long → index = 2
                    # if bitmex porition == none → index = 0
                    taking = 1
                else:
                    taking = 0
            else:
                taking = 0
        elif index == 1:
            if ratio1 > 1 + threshold2:
                # Bitmex open short / Bitstamp buy
                if bitstamp.fetch_balance['info']['usd_available'] > unit * 2:
                    bitmex.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit, price=None)
                    bitstamp.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit_btc, price=None)
                    # if bitmex position == short → index = 1
                    # if bitmex position == long → index = 2
                    # if bitmex porition == none → index = 0
                    taking = 1
                else:
                    taking = 0
            elif ratio1 < 1:
                # Bitmex close short / Bitstamp sell
                if bitstamp.fetch_balance['info']['btc_available'] > unit_btc * 2:
                    bitmex.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit, price=None)
                    bitstamp.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit_btc, price=None)
                    # if bitmex position == short → index = 1
                    # if bitmex position == long → index = 2
                    # if bitmex porition == none → index = 0
                    taking = 1
                else:
                    taking = 0
            else:
                taking = 0
        else:  # index == 2:
            if ratio2 > 1 + threshold2:
                # Bitmex open long / Bitstamp sell
                if bitstamp.fetch_balance['info']['btc_available'] > unit_btc * 2:
                    bitmex.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit, price=None)
                    bitstamp.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit_btc, price=None)
                    # if bitmex position == short → index = 1
                    # if bitmex position == long → index = 2
                    # if bitmex porition == none → index = 0
                    taking = 1
                else:
                    taking = 0
            elif ratio2 < 1:
                # Bitmex close long / Bitstamp buy
                if bitstamp.fetch_balance['info']['usd_available'] > unit * 2:
                    bitmex.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit, price=None)
                    bitstamp.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit_btc, price=None)
                    # if bitmex position == short → index = 1
                    # if bitmex position == long → index = 2
                    # if bitmex porition == none → index = 0
                    taking = 1
                else:
                    taking = 0
            else:
                taking = 0


        ############################## Making Scenario ##############################

        if taking == 0:   # taking이 안돌고 있으면 making을 돌리고, taking이 돌고 있으면 making을 하지 않는다.

            # Initial value setting

            bitmex_open_long_price1 = 0
            bitmex_open_short_price1 = 0
            bitmex_close_long_price1 = 0
            bitmex_close_short_price1 = 0


            # Best price for making - Bistamp 오더북을 보고, Bitmex에 오더북에 마켓메이킹

            bitstamp_bids_sum = 0
            bitstamp_asks_sum = 0

            for i in range(20):
                bitstamp_bids_sum += orderbook_bitstamp['bids'][i][1]
                if bitstamp_bids_sum > amount_btc * orders * (orders + 1) / 2:
                    bitstamp_best_bids = orderbook_bitstamp['bids'][i][0]
                    break

            for i in range(20):
                bitstamp_asks_sum += orderbook_bitstamp['asks'][i][1]
                if bitstamp_asks_sum > amount_btc * orders * (orders + 1) / 2:
                    bitstamp_best_asks = orderbook_bitstamp['asks'][i][0]
                    break

            bitmex_open_long_price = round(bitstamp_best_bids * (1 - threshold1) * 2, 0) / 2
            bitmex_open_short_price = round(bitstamp_best_asks * (1 + threshold1) * 2, 0) / 2
            bitmex_close_long_price = round(bitstamp_best_asks * 2, 0) / 2
            bitmex_close_short_price = round(bitstamp_best_bids * 2, 0) / 2


            bitmex_position_quantity1 = bitmex.fetch_position(symbol='BTC/USD')['currentQty']
            # 0: No position / 1: Bitmex short position / 2: Bitmex long position

            if bitmex_position_quantity1 == 0:
                index = 0
            elif bitmex_position_quantity1 < 0:
                index = 1
            else:   # bitmex_position_quantity > 0:
                index = 2


            # Create making orders

            if index == 0:       # 0: No position / 1: Bitmex short position / 2: Bitmex long position

                # Bitmex open long
                if bitmex_open_long_price == bitmex_open_long_price1:
                    pass
                else:
                    bitmex.cancel_orderall(symbol='BTC/USD', side='buy')
                    bitstamp_btc = bitstamp.fetch_balance['info']['btc_available']
                    if bitstamp_btc > amount_btc * orders * (orders + 1) / 2:
                        if bitmex_best_bids < bitmex_open_long_price:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='buy', amount=amount * orders * (orders + 1) / 2, price=bitmex_best_bids)  # Post Only
                            bitmex_open_long_price1 = bitmex_best_bids
                        else:
                            for i in range(orders):
                                bitmex.create_order(symbol='BTC/USD', type='limit', side='buy', amount=amount * (i + 1), price=bitmex_open_long_price - 0.5 * i)   # Post Only
                                bitmex_open_long_price1 = bitmex_open_long_price
                    else:
                        print("Rebalancing required")

                # Bitmex open short
                if bitmex_open_short_price == bitmex_open_short_price1:
                    pass
                else:
                    bitmex.cancel_orderall(symbol='BTC/USD', side='sell')
                    bitstamp_usd = bitstamp.fetch_balance['info']['usd_available']
                    if bitstamp_usd > amount * orders * (orders + 1) / 2:
                        if bitmex_best_asks > bitmex_open_short_price:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='sell', amount=amount * orders * (orders + 1) / 2, price=bitmex_best_asks)   # Post Only
                            bitmex_open_short_price1 = bitmex_best_asks
                        else:
                            for i in range(orders):
                                bitmex.create_order(symbol='BTC/USD', type='limit', side='sell', amount=amount * (i + 1), price=bitmex_open_short_price + 0.5 * i)   # Post Only
                                bitmex_open_short_price1 = bitmex_open_short_price
                    else:
                        print("Rebalancing required")

            elif index == 1:

                # Bitmex open short
                if bitmex_open_short_price == bitmex_open_short_price1:
                    pass
                else:
                    bitmex.cancel_orderall(symbol='BTC/USD', side='sell')
                    bitstamp_usd = bitstamp.fetch_balance['info']['usd_available']
                    if bitstamp_usd > amount * orders * (orders + 1) / 2:
                        if bitmex_best_asks > bitmex_open_short_price:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='sell', amount=amount * orders * (orders + 1) / 2, price=bitmex_best_asks)  # Post Only
                            bitmex_open_short_price1 = bitmex_best_asks
                        else:
                            for i in range(orders):
                                bitmex.create_order(symbol='BTC/USD', type='limit', side='sell', amount=amount * (i + 1), price=bitmex_open_short_price + 0.5 * i)  # Post Only
                                bitmex_open_short_price1 = bitmex_open_short_price
                    elif bitstamp_usd >= 100:
                        if bitmex_best_asks > bitmex_open_short_price:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='sell', amount=round(bitstamp_usd * 0.9, 0), price=bitmex_best_asks)  # Post Only
                            bitmex_open_short_price1 = bitmex_best_asks
                        else:
                            amount1 = int(2 * bitstamp_usd / (orders * (orders + 1)))
                            for i in range(orders):
                                bitmex.create_order(symbol='BTC/USD', type='limit', side='sell', amount=amount1 * (i + 1) / 2, price=bitmex_open_short_price + 0.5 * i)  # Post Only
                                bitmex_open_short_price1 = bitmex_open_short_price
                    elif bitstamp_usd < 100:
                        if bitmex_best_asks > bitmex_open_short_price:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='sell', amount=round(bitstamp_usd * 0.9, 0), price=bitmex_best_asks)  # Post Only
                            bitmex_open_short_price1 = bitmex_best_asks
                        else:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='sell', amount=round(bitstamp_usd * 0.9, 0), price=bitmex_open_short_price)  # Post Only
                            bitmex_open_short_price1 = bitmex_open_short_price
                    else:
                        pass

                # Bitmex close short
                if bitmex_close_short_price == bitmex_close_short_price1:
                    pass
                else:
                    bitmex.cancel_orderall(symbol='BTC/USD', side='buy')
                    if abs(bitmex_position_quantity1) > amount * orders * (orders + 1) / 2:
                        if bitmex_best_bids < bitmex_close_short_price:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='buy', amount=amount * orders * (orders + 1) / 2, price=bitmex_best_bids)  # Post Only
                            bitmex_close_short_price1 = bitmex_best_bids
                        else:
                            for i in range(orders):
                                bitmex.create_order(symbol='BTC/USD', type='limit', side='buy', amount=amount * (i + 1), price=bitmex_close_short_price - 0.5 * i)  # Post Only
                                bitmex_close_short_price1 = bitmex_close_short_price
                    elif abs(bitmex_position_quantity1) >= 100:
                        if bitmex_best_bids < bitmex_close_short_price:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='buy', amount=abs(bitmex_position_quantity1), price=bitmex_best_bids)  # Post Only
                            bitmex_close_short_price1 = bitmex_best_bids
                        else:
                            amount1 = int(2 * abs(bitmex_position_quantity1) / (orders * (orders + 1)))
                            for i in range(orders):
                                bitmex.create_order(symbol='BTC/USD', type='limit', side='buy', amount=amount1 * (i + 1), price=bitmex_close_short_price - 0.5 * i)  # Post Only
                                bitmex_close_short_price1 = bitmex_close_short_price
                    elif abs(bitmex_position_quantity1) < 100:
                        if bitmex_best_bids < bitmex_close_short_price:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='buy', amount=abs(bitmex_position_quantity1), price=bitmex_best_bids)  # Post Only
                            bitmex_close_short_price1 = bitmex_best_bids
                        else:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='buy', amount=abs(bitmex_position_quantity1), price=bitmex_close_short_price)  # Post Only
                            bitmex_close_short_price1 = bitmex_close_short_price
                    else:
                        pass

            else:   # index == 2:

                # Bitmex open long
                if bitmex_open_long_price == bitmex_open_long_price1:
                    pass
                else:
                    bitmex.cancel_orderall(symbol='BTC/USD', side='buy')
                    bitstamp_btc = bitstamp.fetch_balance['info']['btc_available']
                    if bitstamp_btc > amount_btc * orders * (orders + 1) / 2:
                        if bitmex_best_bids < bitmex_open_long_price:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='buy', amount=amount * orders * (orders + 1) / 2, price=bitmex_best_bids)  # Post Only
                            bitmex_open_long_price1 = bitmex_best_bids
                        else:
                            for i in range(orders):
                                bitmex.create_order(symbol='BTC/USD', type='limit', side='buy', amount=amount * (i + 1), price=bitmex_open_long_price - 0.5 * i)  # Post Only
                                bitmex_open_long_price1 = bitmex_open_long_price
                    elif bitstamp_btc >= 0.01:
                        if bitmex_best_bids < bitmex_open_long_price:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='buy', amount=round(bitstamp_btc * orderbook_bitstamp['bids'][0][0] * 0.9, 0), price=bitmex_best_bids)  # Post Only
                            bitmex_open_long_price1 = bitmex_best_bids
                        else:
                            amount1 = int(2 * bitstamp_btc / (orders * (orders + 1)))
                            for i in range(orders):
                                bitmex.create_order(symbol='BTC/USD', type='limit', side='buy', amount=amount1 * (i + 1) / 2, price=bitmex_open_long_price - 0.5 * i)  # Post Only
                                bitmex_open_long_price1 = bitmex_open_long_price
                    elif bitstamp_btc < 0.01:
                        if bitmex_best_bids < bitmex_open_long_price:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='buy', amount=round(bitstamp_btc * orderbook_bitstamp['bids'][0][0] * 0.9, 0), price=bitmex_best_bids)  # Post Only
                            bitmex_open_long_price1 = bitmex_best_bids
                        else:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='buy', amount=round(bitstamp_btc * orderbook_bitstamp['bids'][0][0] * 0.9, 0), price=bitmex_open_long_price)  # Post Only
                            bitmex_open_long_price1 = bitmex_open_long_price
                    else:
                        pass

                # Bitmex close long
                if bitmex_close_long_price == bitmex_close_long_price1:
                    pass
                else:
                    bitmex.cancel_orderall(symbol='BTC/USD', side='sell')
                    if abs(bitmex_position_quantity1) > amount * orders * (orders + 1) / 2:
                        if bitmex_best_asks > bitmex_close_long_price:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='sell', amount=amount * orders * (orders + 1) / 2, price=bitmex_best_asks)  # Post Only
                            bitmex_close_long_price1 = bitmex_best_asks
                        else:
                            for i in range(orders):
                                bitmex.create_order(symbol='BTC/USD', type='limit', side='sell', amount=amount * (i + 1), price=bitmex_close_long_price + 0.5 * i)  # Post Only
                                bitmex_close_long_price1 = bitmex_close_long_price
                    elif abs(bitmex_position_quantity1) >= 100:
                        if bitmex_best_asks > bitmex_close_long_price:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='sell', amount=abs(bitmex_position_quantity1), price=bitmex_best_asks)  # Post Only
                            bitmex_close_long_price1 = bitmex_best_asks
                        else:
                            amount1 = int(2 * abs(bitmex_position_quantity1) / (orders * (orders + 1)))
                            for i in range(orders):
                                bitmex.create_order(symbol='BTC/USD', type='limit', side='sell', amount=amount1 * (i + 1), price=bitmex_close_long_price + 0.5 * i)  # Post Only
                                bitmex_close_long_price1 = bitmex_close_long_price
                    elif abs(bitmex_position_quantity1) < 100:
                        if bitmex_best_asks > bitmex_close_long_price:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='sell', amount=abs(bitmex_position_quantity1), price=bitmex_best_asks)  # Post Only
                            bitmex_close_long_price1 = bitmex_best_asks
                        else:
                            bitmex.create_order(symbol='BTC/USD', type='limit', side='sell', amount=abs(bitmex_position_quantity1), price=bitmex_close_long_price)  # Post Only
                            bitmex_close_long_price1 = bitmex_close_long_price
                    else:
                        pass


            # Create taking orders after making orders filled

            bitmex_position_quantity = bitmex.fetch_position(symbol='BTC/USD')['currentQty']

            if bitmex_position_quantity1 > bitmex_position_quantity:   # Bitmex short
                bitstamp.create_order(symbol='BTC/USD', type='market', side='buy', amount=round(abs(bitmex_position_quantity1-bitmex_position_quantity)/orderbook_bitstamp['bids'][0][0], 8), price=None)
            elif bitmex_position_quantity1 < bitmex_position_quantity:   # Bitmex long
                bitstamp.create_order(symbol='BTC/USD', type='market', side='sell', amount=round(abs(bitmex_position_quantity1-bitmex_position_quantity)/orderbook_bitstamp['bids'][0][0], 8), price=None)
            else:
                pass

        else:   # taking = 1
            pass

    if index == 0:
        if bitstamp.fetch_balance['info']['usd_available'] > total_usd:
            count = int((bitstamp.fetch_balance['info']['usd_available'] - total_usd) / (orderbook_bitstamp['bids'][0][0]+orderbook_bitstamp['asks'][0][0]) * 2 / unit_btc)
            for i in range(count):
                bitstamp.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit_btc, price=None)
        elif bitstamp.fetch_balance['info']['usd_available'] < total_usd:
            count = int((bitstamp.fetch_balance['info']['usd_available'] - total_usd) / (orderbook_bitstamp['bids'][0][0] + orderbook_bitstamp['asks'][0][0]) * 2 / unit_btc)
            for i in range(count):
                bitstamp.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit_btc, price=None)
        else:
            pass
