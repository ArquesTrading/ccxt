import os
import sys, getopt
import time
root = os.path.dirname(os.path.abspath(__file__))

import asyncio
import ccxt.async_support as ccxt
import dbconnect as db

from elasticsearch import Elasticsearch
from elasticsearch import helpers



async def async_client(exchange_name, symbol):
    if exchange_name == 'coinbase':
        exchange_name = 'coinbasepro'

    if exchange_name == 'huobiswap':
        symbol = symbol.replace('/','-')

    if exchange_name == 'okex':
        symbol = symbol.replace('/','-') + '-SWAP'
      
    client = getattr(ccxt, exchange_name)()
    ticker = await client.fetch_ticker(symbol)
    await client.close()
    # return ticker
    return set_value_by_ticker(exchange_name, ticker)

def set_value_by_ticker(exchnage_name, ticker):
    dic = {}
    dic['exchange_name'] = exchnage_name
    dic['symbol'] = ticker["symbol"]
    dic['timestamp'] = ticker['timestamp']
    dic['datetime'] = ticker['datetime']
    dic['open'] = check_none_value(ticker['open'])
    dic['high'] = check_none_value(ticker['high'])
    dic['low'] = check_none_value(ticker['low'])
    dic['close'] = check_none_value(ticker['close'])
    dic['volume'] = check_none_value(ticker['baseVolume'])

    return dic

def check_none_value(value):
    if value is None:
        value = 0
    
    return value

async def multi_ticker():
    while True:
        exchanges = ["bitmex", "coinbase", "bitstamp", 'huobiswap', 'okex']
        symbol = "BTC/USD"
        input_tickers = [async_client(exchange_name, symbol) for exchange_name in exchanges]
        tickers = await asyncio.gather(*input_tickers, return_exceptions=True)

        # print(tickers)
        # print('aaa')
        # await asyncio.sleep(1)
        await insert(tickers)


async def insert(data):

    server = 'http://es-arques.com:9200/'
    index_name = 'crypto_price_info'
    # # elasticsearch connect
    es = Elasticsearch(server)
    es.info()

    if len(data) > 0:
        for li in data:
            _exchange_name = li['exchange_name']
            _symbol = li['symbol']
            _period = 'ticksync'
            _timestamp = li['timestamp']
            _datetime = li['datetime']
            _open = check_none_value(li['open'])
            _high = check_none_value(li['high'])
            _low = check_none_value(li['low'])
            _close = check_none_value(li['close'])
            _volume = check_none_value(li['volume'])

            params = (_exchange_name, _symbol, _period, _timestamp, _datetime, _open, _high, _low, _close, _volume)
            r = db.insert_price(_exchange_name, params)

            es.index(index=index_name, doc_type='string', body=li)

    es.indices.refresh(index=index_name)


    t = time.time()
    print(t, 'Ticker starting from', data)


    await asyncio.sleep(2)



def stop():
    task.cancel()


loop = asyncio.get_event_loop()
# loop.call_later(10, stop)
task = loop.create_task(multi_ticker())

try:
    loop.run_until_complete(task)
except asyncio.CancelledError:
    pass