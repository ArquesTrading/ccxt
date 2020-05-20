import os
import sys, getopt
import time
root = os.path.dirname(os.path.abspath(__file__))


import ccxt
# import ccxt.async_support as ccxt
import dbconnect as db
import db_crypto_read as cryptodb
import asyncio


# ------------------------------------------------------------

unit = 100              # in US Dollar
threshold = 0.002       # 0.0n refers to n%
index = 0               # bimex position 0: No position / 1: Bitmex short position / 2: Bitmex long position


# ------------------------------------------------------------


def get_orderbook(exchange_name, symbol):
    if exchange_name == 'coinbase':
        exchange_name = 'coinbasepro'

    if exchange_name == 'huobiswap':
        symbol = symbol.replace('/','-')

    if exchange_name == 'okex':
        symbol = symbol.replace('/','-') + '-SWAP'
      
    orderbook = cryptodb.get_order_book_data(exchange_name, symbol)    
    return orderbook

def get_bitmex_position():
    bitmex = ccxt.bitmex({
        'apiKey': 'b4elbldRv7YfqbA1xyI2LVMD',
        'secret': 'dhcdtj_N8-2Eqj29DeaC0h2j8ksm_q_vB_zVDq5g2kr3iLpU',
    })
    if 'test' in exchange.urls:
        exchange.urls['api'] = exchange.urls['test'] # ←----- switch the base URL to testnet

    position = bitmex.fetch_position()
    
    if position[0]["currentQty"] == 0:
        return 0
    elif position[0]["currentQty"] < 0:
        return 1
    elif position[0]["currentQty"] > 0:
        return 2



def trading():
    while True:
        global index
        global unit
        global threshold

        exchanges = ["bitmex", "bitstamp"]
        symbol = "BTC/USD"

        orderbooks = {}

        for exchange_name in exchanges:
            orderbook = get_orderbook(exchange_name, symbol)
            orderbooks[exchange_name] = orderbook

        # order book 
        orderbook_bitmex = orderbooks["bitmex"]
        orderbook_bitstamp = orderbooks["bitstamp"]

        # get executing timestamp
        timestamp = orderbook_bitmex["timestamp"]

        print(timestamp, " trading process start!! ")

        # 0.00000001 BTC = 1 satoshi 로 unit_satoshi 계산
        unit_satoshi = round(unit/orderbook_bitstamp['bids'][0]['price'], 8)

        # Target Price

        bitmex_bids_sum = 0
        bitmex_asks_sum = 0
        bitstamp_bids_sum = 0
        bitstamp_asks_sum = 0

        for i in range(len(orderbook_bitmex)):
            bitmex_bids_sum += orderbook_bitmex['bids'][i]['volume']
            if bitmex_bids_sum > unit:
                bitmex_bids_no = i
                break

        for i in range(len(orderbook_bitmex)):
            bitmex_asks_sum += orderbook_bitmex['asks'][i]['volume']
            if bitmex_asks_sum > unit:
                bitmex_asks_no = i
                break

        for i in range(len(orderbook_bitstamp)):
            bitstamp_bids_sum += orderbook_bitstamp['bids'][i]['volume']
            if bitstamp_bids_sum > unit_satoshi:
                bitstamp_bids_no = i
                break

        for i in range(len(orderbook_bitstamp)):
            bitstamp_asks_sum += orderbook_bitstamp['asks'][i]['volume']
            if bitstamp_asks_sum > unit_satoshi:
                bitstamp_asks_no = i
                break

        print(unit, unit_satoshi, bitmex_bids_no, bitmex_asks_no, bitstamp_bids_no, bitstamp_asks_no)


        # Create Orders

        # index = 0       # 0: No position / 1: Bitmex short position / 2: Bitmex long position

        ratio1 = round(orderbook_bitmex['bids'][bitmex_bids_no]["price"] / orderbook_bitstamp['asks'][bitstamp_asks_no]["price"], 8)
        ratio2 = round(orderbook_bitstamp['bids'][bitstamp_bids_no]["price"] / orderbook_bitmex['asks'][bitmex_asks_no]["price"], 8)

        checker1 = 1 + threshold

        # print(timestamp, ' NOW STATUS :: index = ', index, ', threshold = ', threshold, ', ratio1 = ', ratio1, ', ratio2 = ', ratio2, ', check1 = ', checker1)

        if index == 0:
            if ratio1 > 1 + threshold:
                # print(index, ratio1, 1 + threshold, 'Bitmex open short / Bitstamp buy')
                order_comment = 'bitmex sell : ' + str(unit) + ', bitstamp buy : ' + str(unit_satoshi)
                params = (timestamp, 'trading_v1', index, ratio1, ratio2, 'Bitmex open short / Bitstamp buy', order_comment)
                db.insert_trading_log(params)
                index = 1

                # 정보 가져와서 오더 한 뒤
                # position 가져와서 currentQty 이게 양수면 2 , 음수면 1, 0이면 0
                # 백테스트는 bitmex 만 우선 진행 해봄.

                # # Bitmex open short / Bitstamp buy                
                # if bitstamp.fetch_balance['info']['usd_available'] > unit * 2:
                #     bitmex.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit, price=None)
                #     bitstamp.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit_satoshi, price=None)

                #     index = get_bitmex_position()                    
                    
                #     # if bitmex position == short → index = 1
                #     # if bitmex position == long → index = 2
                #     # if bitmex porition == none → index = 0
                # else:
                #     pass
            elif ratio2 > 1 + threshold:
                # print(index, ratio2, 1 + threshold, 'Bitmex open long / Bitstamp sell')
                order_comment = 'bitmex buy : ' + str(unit) + ', bitstamp sell : ' + str(unit_satoshi)
                params = (timestamp, 'trading_v1', index, ratio1, ratio2, 'Bitmex open long / Bitstamp sell', order_comment)
                db.insert_trading_log(params)
                index = 2
                # Bitmex open long / Bitstamp sell

                # if bitstamp.fetch_balance['info']['btc_available'] > unit_satoshi * 2:
                #     bitstamp.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit_satoshi, price=None)
                #     bitmex.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit, price=None)

                #     index = get_bitmex_position()

                #     # if bitmex position == short → index = 1
                #     # if bitmex position == long → index = 2
                #     # if bitmex porition == none → index = 0
                # else:
                #     pass
            else:
                pass
        elif index == 1:
            if ratio1 > 1 + threshold:
                # print(index, ratio1, 1 + threshold, 'Bitmex open short / Bitstamp buy')
                order_comment = 'bitmex sell : ' + str(unit) + ', bitstamp buy : ' + str(unit_satoshi)
                params = (timestamp, 'trading_v1', index, ratio1, ratio2, 'Bitmex open short / Bitstamp buy', order_comment)
                db.insert_trading_log(params)
                index = 1
                # Bitmex open short / Bitstamp buy
                # if bitstamp.fetch_balance['info']['usd_available'] > unit * 2:
                #     bitmex.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit, price=None)
                #     bitstamp.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit_satoshi, price=None)
                #     # if bitmex position == short → index = 1
                #     # if bitmex position == long → index = 2
                #     # if bitmex porition == none → index = 0
                # else:
                #     pass
            elif ratio1 < 1:
                # print(index, ratio1, 1, 'Bitmex close short / Bitstamp sell')
                order_comment = 'bitmex buy : ' + str(unit) + ', bitstamp sell : ' + str(unit_satoshi)
                params = (timestamp, 'trading_v1', index, ratio1, ratio2, 'Bitmex close short / Bitstamp sell', order_comment)
                db.insert_trading_log(params)
                index = 0
                # # Bitmex close short / Bitstamp sell
                # if bitstamp.fetch_balance['info']['btc_available'] > unit_satoshi * 2:
                #     bitmex.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit, price=None)
                #     bitstamp.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit_satoshi, price=None)
                #     # if bitmex position == short → index = 1
                #     # if bitmex position == long → index = 2
                #     # if bitmex porition == none → index = 0
                # else:
                #     pass
            else:
                pass
        elif index == 2:
            if ratio2 > 1 + threshold:
                # print(index, ratio2, 1 + threshold, 'Bitmex open long / Bitstamp sell')
                order_comment = 'bitmex buy : ' + str(unit) + ', bitstamp sell : ' + str(unit_satoshi)
                params = (timestamp, 'trading_v1', index, ratio1, ratio2, 'Bitmex open long / Bitstamp sell', order_comment)
                db.insert_trading_log(params)
                index = 2
                # # Bitmex open long / Bitstamp sell
                # if bitstamp.fetch_balance['info']['btc_available'] > unit_satoshi * 2:
                #     bitmex.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit, price=None)
                #     bitstamp.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit_satoshi, price=None)
                #     # if bitmex position == short → index = 1
                #     # if bitmex position == long → index = 2
                #     # if bitmex porition == none → index = 0
                # else:
                #     pass
            elif ratio2 < 1:
                # print(index, ratio2, 1, 'Bitmex close long / Bitstamp buy')
                order_comment = 'bitmex sell : ' + str(unit) + ', bitstamp buy : ' + str(unit_satoshi)
                params = (timestamp, 'trading_v1', index, ratio1, ratio2, 'Bitmex close long / Bitstamp buy', order_comment)
                db.insert_trading_log(params)
                index = 0
                # # Bitmex close long / Bitstamp buy
                # if bitstamp.fetch_balance['info']['usd_available'] > unit * 2:
                #     bitmex.create_order(symbol='BTC/USD', type='market', side='sell', amount=unit, price=None)
                #     bitstamp.create_order(symbol='BTC/USD', type='market', side='buy', amount=unit_satoshi, price=None)
                #     # if bitmex position == short → index = 1
                #     # if bitmex position == long → index = 2
                #     # if bitmex porition == none → index = 0
                # else:
                #     pass
            else:
                pass
        else:
            pass


# async def trading_process(orderbooks):
#     print(orderbooks)


# ------------------------------------------------------------
# 시작
# ------------------------------------------------------------
# loop = asyncio.get_event_loop()
# task = loop.create_task(trading())

# try:
#     loop.run_until_complete(task)
# except asyncio.CancelledError:
#     pass

trading()