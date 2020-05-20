import os
import sys, getopt
import time
root = os.path.dirname(os.path.abspath(__file__))

import ccxt
import dbconnect as db
import threading
import mongoconnect as mongo

# orderbook 를 input 받은 거래소와 input 받은 symbol 기준으로 가져와서 SQL Server 에 저장하기

# -----------------------------------------------------------------------------

exchange = ccxt.bitmex()

from_timestamp = time.time()

exchange_name = ""
symbol = ""
threadtimesecond = 5
from_datetime = ""


# -----------------------------------------------------------------------------


def get_exchange(id):
    if id == 'coinbase':
        id = 'coinbasepro'

    if id == 'huobi':
        id = 'huobiswap'
      
    exchange = getattr(ccxt, id)({
        'rateLimit': 3000,
        'enableRateLimit' : True,
    })
    return exchange



def main(argv):
    FILE_NAME = argv[0]
    

    try:
        opts, etc_args = getopt.getopt(argv[1:], \
                                 "he:s:t:", ["help","exchange_name=","symbol=","threadtime="])
    
    except getopt.GetoptError: # 옵션지정이 올바르지 않은 경우
        print(FILE_NAME, '-e <exchange name> -s <symbol> -t <threadtime>')
        sys.exit(2)

    for opt, arg in opts: # 옵션이 파싱된 경우
        if opt in ("-h", "--help"): # HELP 요청인 경우 사용법 출력
            print(FILE_NAME, '-e <exchange name> -s <symbol> -t <threadtime>')
            sys.exit()

        elif opt in ("-e", "--exchange"): # 거래소 명 입력인 경우
            exchange_name = arg

        elif opt in ("-s", "--symbol"): # 시작일자 입력인 경우
            symbol = arg
        elif opt in ("-t", "--threadtime"): # thread 초 단위
            threadtimesecond = int(arg)

    if len(exchange_name) < 1: # 필수항목 값이 비어있다면
        print(FILE_NAME, "-e 거래소명은 반드시 입력 바랍니다. ( bitmex, coinbase )") # 필수임을 출력
        sys.exit(2)

    if len(symbol) < 1:
        print(FILE_NAME, "-s 심볼은 반드시 입력 바랍니다. (BTC/USD, ... )") # 필수임을 출력
        sys.exit(2)

    # exchange_name = 'bitmex'
    # symbol = 'BTC/USD'
    # threadtimesecond = 1

    if exchange_name == 'huobi':
        symbol = symbol.replace('/','-')
    
    # 여기서 부터 시작
    print('gogo')

    crawling(exchange_name, symbol, threadtimesecond)


def crawling(exchange_name, symbol, threadtimesecond):    
    threading.Timer(threadtimesecond, crawling, [exchange_name, symbol, threadtimesecond]).start()

    exchange = get_exchange(exchange_name)    
    
    nowstamp = exchange.milliseconds()
    nowtime = exchange.iso8601(nowstamp)
    orderbook = exchange.fetch_order_book(symbol, limit=20)

    # print(nowstamp)
    # print(nowtime)
    # print(orderbook)

    
    # 가져온 order book 를 Sql Server 에 저장하기
    insert(exchange_name, symbol, nowstamp, nowtime, orderbook)

def check_none_value(value):
    if value is None:
        value = 0
    
    return value

# -----------------------------------------------------------------------------


def insert(exchange_name, symbol, timestamp, nowtime, data):

    bids = data["bids"]
    asks = data["asks"]

    _data = {}
    _data["exchange"] = exchange_name
    _data["symbol"] = symbol
    _data["timestamp"] = timestamp
    _data["nowtime"] = nowtime
    _data["bids"] = bids
    _data["asks"] = asks

    mongo.insert('crypto', 'crypto_order_book', _data)

    # bids 저장
    for i in range(20):
        _price = check_none_value(bids[i][0])
        _volume = check_none_value(bids[i][1])

        params = (exchange_name, symbol, timestamp, nowtime, 'bids', i, _price, _volume)
        db.insert_order_book(params)
    
    # asks 저장
    for i in range(20):
        _price = check_none_value(asks[i][0])
        _volume = check_none_value(asks[i][1])

        params = (exchange_name, symbol, timestamp, nowtime, 'asks', i, _price, _volume)
        db.insert_order_book(params)        
    
    print(timestamp, exchange_name, 'Order Book starting from', nowtime)

# -----------------------------------------------------------------------------


# module이 아닌 main으로 실행된 경우 실행된다
if __name__ == "__main__":
    main(sys.argv)



