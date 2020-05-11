import os
import sys, getopt
import time

import ccxt
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
    #symbol = 'BTC/USD'
    
    # 여기서 부터 시작
    print('gogo')

    crawling(exchange_name, symbol)



def crawling(exchange_name, symbol):    
    threading.Timer(5.0, crawling, [exchange_name, symbol]).start()

    exchange = get_exchange(exchange_name)    
    ticker = exchange.fetch_ticker(symbol)
    
    #print(exchange.name)
    #print(ticker)
    insert(exchange_name, symbol, ticker)

def check_none_value(value):
    if value is None:
        value = 0
    
    return value


# -----------------------------------------------------------------------------


def insert(exchange_name, symbol, data):
    _timestamps = data["timestamp"]
    _datetime = data["datetime"]
    _open = check_none_value(data["open"])
    _high = check_none_value(data["high"])
    _low = check_none_value(data["low"])
    _close = check_none_value(data["close"])
    _baseVolume = check_none_value(data["baseVolume"])

    params = (exchange_name, symbol, _timestamps, _datetime, _open, _high, _low, _close, _baseVolume)
    r = db.insert_price(exchange_name, params)
    #print(params, r)
    print(data["timestamp"], exchange_name, 'Ticker starting from', data["datetime"])


# -----------------------------------------------------------------------------


# module이 아닌 main으로 실행된 경우 실행된다
if __name__ == "__main__":
    main(sys.argv)



