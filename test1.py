
import os
import sys
import time
#root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
root = os.path.dirname(os.path.abspath(__file__))

import ccxt

import threading

def get_ticker():
    threading.Timer(2.0, get_ticker).start()

    exchange = ccxt.bitstamp({
        'rateLimit': 3000,
        'enableRateLimit' : True,
    })

    symbol = 'BTC/USD'
    
    #ticker = exchange.fetch_ticker(symbol)
    #print(ticker)
    order_book = exchange.fetch_order_book(symbol, 10)
    print(order_book)


get_ticker()



#print(root)
#sys.path.append(root + '/python')