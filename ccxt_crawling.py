import os
import sys, getopt
import time
root = os.path.dirname(os.path.abspath(__file__))

import ccxt
import dbconnect as db


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
                                 "he:f:", ["help","exchange_name=","from_datetime="])
    
    except getopt.GetoptError: # 옵션지정이 올바르지 않은 경우
        print(FILE_NAME, '-e <exchange name> -f <from dateTime>')
        sys.exit(2)

    for opt, arg in opts: # 옵션이 파싱된 경우
        if opt in ("-h", "--help"): # HELP 요청인 경우 사용법 출력
            print(FILE_NAME, '-e <exchange name> -f <from dateTime>')
            sys.exit()

        elif opt in ("-e", "--exchange"): # 거래소 명 입력인 경우
            exchange_name = arg

        elif opt in ("-f", "--from"): # 시작일자 입력인 경우
            from_datetime = arg + ' 00:00:00'

    if len(exchange_name) < 1: # 필수항목 값이 비어있다면
        print(FILE_NAME, "-e 거래소명은 반드시 입력 바랍니다. ( bitmex, coinbase )") # 필수임을 출력
        sys.exit(2)

    if len(from_datetime) < 1:
        from_datetime = '2020-05-07 00:00:00'

    

    print("exchange_name:", exchange_name)
    print("from_datetime:",  from_datetime)

    # 여기서 부터 시작
    print('gogo')

    exchange = get_exchange(exchange_name)
    symbol = 'BTC/USD'

    if exchange_name == 'bitmex':
        # exchange = ccxt.bitmex({
        #     'rateLimit': 3000,
        #     'enableRateLimit' : True,
        # })
        # symbol = 'BTC/USD'
        unit = 200
    elif exchange_name == 'coinbase':
        # exchange = ccxt.coinbasepro({
        #     'rateLimit': 3000,
        #     'enableRateLimit': True,
        #     # 'verbose': True,
        # })
        # symbol = 'BTC/USD'
        unit = 300

    from_timestamp = exchange.parse8601(from_datetime)
    now = exchange.milliseconds()

    print(exchange.name)
    print(symbol)
    print(from_timestamp)
    print(now)
        
    while from_timestamp < now:

        try:

            print(exchange.milliseconds(), exchange.name, 'Fetching candles starting from', exchange.iso8601(from_timestamp))
            ohlcvs = exchange.fetch_ohlcv(symbol, '1m', from_timestamp, unit)
            print(exchange.milliseconds(), exchange.name, 'Fetched', len(ohlcvs), 'candles')
            from_timestamp = ohlcvs[-1][0]
            if len(ohlcvs) > 1:
                insert(exchange_name, symbol, ohlcvs)
                time.sleep(10)
            else:
                time.sleep(30)

            now = exchange.milliseconds()
            

        except (ccxt.ExchangeError, ccxt.AuthenticationError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as error:

            print('Got an error', type(error).__name__, error.args, ', retrying in', hold, 'seconds...')
            time.sleep(hold)




# -----------------------------------------------------------------------------


def check_none_value(value):
    if value is None:
        value = 0
    
    return value



def insert(exchange_name, symbol, list):
    if len(list) > 0:
        for li in list:
            _period = '1m'
            ts = li[0]
            d = exchange.iso8601(ts)
            # li.insert(1, d)
            # li.insert(0, exchange_name)
            # li.insert(1, symbol)
            # li.insert(2, _period)

            _timestamp = li[0]
            _datetime = d            
            _open = check_none_value(li[1])
            _high = check_none_value(li[2])
            _low = check_none_value(li[3])
            _close = check_none_value(li[4])
            _baseVolume = check_none_value(li[5])

            # params = (li[0], li[1], li[2], li[3], li[4], li[5], li[6], li[7], li[8], li[9])
            params = (exchnage_name, symbol, _period, _timestamp, _datetime, _open, _high, _low, _close, _baseVolume)
            
            # print(params)
            if li[4] is not None:
                r = db.insert_price(exchange_name, params)
                # print(r)


# -----------------------------------------------------------------------------


# module이 아닌 main으로 실행된 경우 실행된다
if __name__ == "__main__":
    main(sys.argv)



