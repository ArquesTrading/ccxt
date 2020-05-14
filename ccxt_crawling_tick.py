import os
import sys, getopt
import time
root = os.path.dirname(os.path.abspath(__file__))

import asyncio
import ccxt
import ccxt.async_support as ccxta
import dbconnect as db
import threading


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
    

    try:
        opts, etc_args = getopt.getopt(argv[1:], \
                                 "he:s:", ["help","exchange_name=","symbol="])
    
    except getopt.GetoptError: # 옵션지정이 올바르지 않은 경우
        print(FILE_NAME, '-e <exchange name> -s <symbol>')
        sys.exit(2)

    for opt, arg in opts: # 옵션이 파싱된 경우
        if opt in ("-h", "--help"): # HELP 요청인 경우 사용법 출력
            print(FILE_NAME, '-e <exchange name> -s <symbol>')
            sys.exit()

        elif opt in ("-e", "--exchange"): # 거래소 명 입력인 경우
            exchange_name = arg

        elif opt in ("-s", "--symbol"): # 시작일자 입력인 경우
            symbol = arg

    # if len(exchange_name) < 1: # 필수항목 값이 비어있다면
    #     print(FILE_NAME, "-e 거래소명은 반드시 입력 바랍니다. ( bitmex, coinbase )") # 필수임을 출력
    #     sys.exit(2)

    # if len(symbol) < 1:
    #     print(FILE_NAME, "-s 심볼은 반드시 입력 바랍니다. (BTC/USD, ... )") # 필수임을 출력
    #     sys.exit(2)

    #exchange_name = 'coinbase'
    symbol = 'BTC/USD'
    
    # 여기서 부터 시작
    print('gogo')

    crawling(symbol)



def crawling(symbol):    
    # threading.Timer(5.0, crawling, [symbol]).start()

    exchanges = ["bitmex", "coinbase", "bitstamp"]

    loop = asyncio.get_event_loop()
    #loop.call_later(5, stop)
    task = loop.create_task(multi_ticker(exchanges, symbol))

    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass        

    # tic = time.time()
    # a = asyncio.get_event_loop().run_until_complete(multi_ticker(exchanges, symbol))
    # print(a)
    # print("async call spend:", time.time() - tic)

    # exchange = get_exchange(exchange_name)    
    # ticker = exchange.fetch_ticker(symbol)
    
    # #print(exchange.name)
    # #print(ticker)
    # insert(exchange_name, symbol, ticker)

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
        print(tickers)
        await asyncio.sleep(1)


def stop():
    task.cancle()


def check_none_value(value):
    if value is None:
        value = 0
    
    return value


# -----------------------------------------------------------------------------


def insert(exchange_name, symbol, data):
    _period = 'tick'
    _timestamps = data["timestamp"]
    _datetime = data["datetime"]
    _open = check_none_value(data["open"])
    _high = check_none_value(data["high"])
    _low = check_none_value(data["low"])
    _close = check_none_value(data["close"])
    _baseVolume = check_none_value(data["baseVolume"])

    params = (exchange_name, symbol, _period, _timestamps, _datetime, _open, _high, _low, _close, _baseVolume)
    r = db.insert_price(exchange_name, params)
    #print(params, r)
    print(data["timestamp"], exchange_name, 'Ticker starting from', data["datetime"])


# -----------------------------------------------------------------------------


# module이 아닌 main으로 실행된 경우 실행된다
if __name__ == "__main__":
    main(sys.argv)

