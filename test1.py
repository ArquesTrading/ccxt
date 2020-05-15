
import os
import sys
import time
root = os.path.dirname(os.path.abspath(__file__))

import ccxt

import threading

def get_ticker():
    threading.Timer(1.0, get_ticker).start()

    exchange = ccxt.okex({
        'rateLimit': 3000,
        'enableRateLimit' : True,
    })

    # tickers = exchange.fetch_ticker('BTC-USD')
    # print(tickers)

    # tickers = exchange.fetch_tickers(params={'type':'swap'})
    # for i in tickers.keys():
    #     print(i)
    tick = exchange.fetch_ticker('BTC-USD-SWAP')
    print(tick['symbol'], tick['close'])

    # symbol = 'BTC/USD'
    
    #ticker = exchange.fetch_ticker(symbol)
    #print(ticker)
    # order_book = exchange.fetch_order_book(symbol, 10)
    # print(order_book)


get_ticker()

