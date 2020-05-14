import os
import sys, getopt
import time
root = os.path.dirname(os.path.abspath(__file__))

import asyncio
import ccxt
import ccxt.async_support as ccxta
import dbconnect as db
import threading

from elasticsearch import Elasticsearch
from elasticsearch import helpers

# ticker 자료를 비동기 로 여러개의 거래소의 자료를 한 프로세스에서 가져오기. 

# -----------------------------------------------------------------------------
# common constants

msec = 1000
minute = 60 * msec
hold = 30
unit = 240

# -----------------------------------------------------------------------------


exchange = ccxt.bitmex({
    'rateLimit': 3000,
    'enableRateLimit' : True,
})

from_timestamp = time.time()

exchange_name = ""
symbol = ""
from_datetime = ""

# -----------------------------------------------------------------------------

def get_exchange(id):
    if id == 'coinbase':
        id = 'coinbasepro'
      
    exchange = getattr(ccxt, id)({
        'rateLimit': 3000,
        'enableRateLimit' : True,
    })
    return exchange

def get_a_exchange(id):
    if id == 'coinbase':
        id = 'coinbasepro'
      
    exchange = getattr(ccxta, id)({
        'rateLimit': 3000,
        'enableRateLimit' : True,
    })
    return exchange

def main(argv):
    FILE_NAME = argv[0]
    
    symbol = 'BTC/USD'
    
    # 여기서 부터 시작
    print('gogo')

    crawling(symbol)



def crawling(symbol):    
    exchanges = ["bitmex", "coinbase", "bitstamp"]

    loop = asyncio.get_event_loop()
    task = loop.create_task(multi_ticker(exchanges, symbol))

    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass        


async def async_client(exchange_name, symbol):
    if exchange_name == 'coinbase':
        exchange_name = 'coinbasepro'
      
    client = getattr(ccxta, exchange_name)()
    ticker = await client.fetch_ticker(symbol)
    await client.close()
    
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
    dic['volume'] = check_none_value(ticker['info']['volume'])

    return dic


async def multi_ticker(exchanges, symbol):
    while True:
        input_tickers = [async_client(exchange_name, symbol) for exchange_name in exchanges]
        tickers = await asyncio.gather(*input_tickers, return_exceptions=True)        
        # 한꺼번에 가져온 ticker 자료를 Sql server 와 Elasticsearch 에 저장하기
        await insert(tickers)
        
    

def check_none_value(value):
    if value is None:
        value = 0
    
    return value


# -----------------------------------------------------------------------------


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
            r = db.insert_price(exchange_name, params)

            es.index(index=index_name, doc_type='string', body=li)

    es.indices.refresh(index=index_name)


    t = time.time()
    print(t, 'Ticker starting from', data)


    await asyncio.sleep(1)


# -----------------------------------------------------------------------------


# module이 아닌 main으로 실행된 경우 실행된다
if __name__ == "__main__":
    main(sys.argv)

