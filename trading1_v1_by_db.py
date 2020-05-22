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

unit = 100                      # in US Dollar
threshold = 0.002               # 0.0n refers to n%
index = 0                       # bimex position 0: No position / 1: Bitmex short position / 2: Bitmex long position
fees = 0.08                     # 수수료
trading_name = 'trading_v1'     # 트레이딩알고리즘 이름
step = 8

for_timestamp = 1589796068930   # 테스트 시작 timestamp
for_datetime = '2020-05-18'     # for_timestamp 가 0으로 할 경우 날짜 기준으로 

futures_btc_balance = 3         # bitmex 코인보유량 구매시 - 팔경우 + 
futures_usd_balance = 0         # bitmex 
futures_size = 0                 # bitmex Size = futures_usd_balance * -1
spot_btc_balance = 3            # bitstamp 코인보유량
spot_usd_balance = 30000        # bitstamp 달러보유량



# ------------------------------------------------------------

# DB에 저장되어 있는 오더북 조회 ( 우선 스냅샷 찍힌 자료로 처리, socket 으로 현재 orderbook 가져와서 realtime orderbook 으로 수정할 예정 )
def get_orderbook(exchange_name, symbol, timestamp):
    if exchange_name == 'coinbase':
        exchange_name = 'coinbasepro'

    if exchange_name == 'huobiswap':
        symbol = symbol.replace('/','-')

    if exchange_name == 'okex':
        symbol = symbol.replace('/','-') + '-SWAP'
      
    orderbook = cryptodb.get_order_book_data(exchange_name, symbol, timestamp)    
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

# 0.00000001 BTC = 1 satoshi 로 unit_satoshi 계산
def get_satoshi(unit, price):
    return round(unit/price, 8)

# orderbook 을 기준으로 order 내릴 가격 정보 위치 파악하기
def get_orderbook_idx(exchange,unit):    
    bids_sum = 0
    asks_sum = 0
    bids_no = 0
    asks_no = 0

    unit_compare = unit
    if exchange["type"] == 'spot':
        unit_compare = get_satoshi(unit, exchange["orderbook"]['bids'][0]['price'])


    for i in range(len(exchange["orderbook"])):
            bids_sum += exchange["orderbook"]['bids'][i]['volume']
            if bids_sum > unit_compare:
                bids_no = i
                break
    for i in range(len(exchange["orderbook"])):
            asks_sum += exchange["orderbook"]['asks'][i]['volume']
            if asks_sum > unit_compare:
                asks_no = i
                break
    exchange["bids_no"] = bids_no
    exchange["asks_no"] = asks_no
    return exchange

# 각 거래소에 오더 처리 ( live 는 구매할 대상 수만 파악해서 마켓가로 order, test 는 현재 자산가치 등을 계산해서 log 남김 )
def create_order(exchanges, futures_action, spot_action):
    global index
    global unit
    global threshold
    
    global trading_name
    global step
    global fees
            
    global futures_btc_balance
    global futures_usd_balance
    global spot_btc_balance
    global spot_usd_balance

    futures_unit_satoshi = 0
    spot_unit_satoshi = 0
    futures_bids_no = exchanges['futures']['bids_no']
    futures_asks_no = exchanges['futures']['asks_no']
    spot_bids_no = exchanges['spot']['bids_no']
    spot_asks_no = exchanges['spot']['asks_no']
    futures_sell_price = exchanges['futures']['orderbook']['bids'][futures_bids_no]['price']
    futures_buy_price = exchanges['futures']['orderbook']['asks'][futures_asks_no]['price']
    spot_sell_price = exchanges['spot']['orderbook']['asks'][spot_asks_no]['price']
    spot_buy_price = exchanges['spot']['orderbook']['bids'][spot_bids_no]['price']
    futures_action_price = 0
    spot_action_price = 0

    from_index = index
    to_index = 0

    timestamp = exchanges["futures"]["orderbook"]["timestamp"]                
    

    if futures_action == 'sell':
        futures_unit_satoshi = get_satoshi(unit, futures_sell_price) 
        futures_btc_balance = futures_btc_balance - futures_unit_satoshi
        futures_usd_balance = futures_usd_balance + unit
        futures_action_price = futures_sell_price
    elif futures_action == 'buy':
        futures_unit_satoshi = get_satoshi(unit, futures_buy_price)
        futures_btc_balance = futures_btc_balance + futures_unit_satoshi
        futures_usd_balance = futures_usd_balance - unit
        futures_action_price = futures_buy_price
    else:
        pass

    if spot_action == 'sell':
        # spot_unit_satoshi = get_satoshi(unit, spot_sell_price)
        spot_unit_satoshi = get_satoshi(unit, exchanges['spot']['orderbook']['bids'][0]['price'])
        spot_btc_balance = spot_btc_balance - spot_unit_satoshi
        spot_usd_balance = spot_usd_balance + spot_unit_satoshi * spot_sell_price
        spot_action_price = spot_sell_price
    elif spot_action == 'buy':
        # spot_unit_satoshi = get_satoshi(unit, spot_buy_price)
        spot_unit_satoshi = get_satoshi(unit, exchanges['spot']['orderbook']['bids'][0]['price'])
        spot_btc_balance = spot_btc_balance + spot_unit_satoshi
        spot_usd_balance = spot_usd_balance - spot_unit_satoshi * spot_buy_price
        spot_action_price = spot_buy_price
    else:
        pass

    # 선물거래소의 usd 자산을 가지고 현재 position 계산 ( 0: No position / 1: Bitmex short position / 2: Bitmex long position )
    if futures_usd_balance * -1 == 0:
        to_index = 0
    elif futures_usd_balance * -1 < 0:
        to_index = 1
    elif futures_usd_balance * -1 > 0:
        to_index = 2
    
    # 테스트 용은 로그 남김 ( live 에는 거래소에 market가격으로 오더 )
    order_comment = ''
    params = (trading_name, timestamp, step, threshold, fees, futures_btc_balance, futures_usd_balance, spot_btc_balance, spot_usd_balance, exchanges['futures']['exchange_name'], futures_action, futures_action_price, unit,exchanges['spot']['exchange_name'],spot_action, spot_action_price, spot_unit_satoshi, from_index,to_index,0,0,unit,futures_unit_satoshi,futures_bids_no,futures_asks_no,spot_bids_no,spot_asks_no,order_comment, 0)
    db.insert_trading_log_v2(params)

    index = to_index

# 트레이딩 알고리즘 메소드
def trading(exchanges):
    while True:
        global index
        global unit
        global threshold

        global for_timestamp
        global for_datetime

        global trading_name
        global step
        global fees
                
        global futures_btc_balance
        global futures_usd_balance
        global spot_btc_balance
        global spot_usd_balance        

        orderbooks = {}

        # exchanges 의 order book 가져와서 unit 에 대한 orderbook idx 를 가져오기
        for key in exchanges.keys():            
            orderbooks = get_orderbook(exchanges[key]["exchange_name"], exchanges[key]["symbol"], for_timestamp)
            exchanges[key]["orderbook"] = orderbooks
            exchanges[key] = get_orderbook_idx(exchanges[key], unit)

        # get executing timestamp
        timestamp = exchanges["futures"]["orderbook"]["timestamp"]

        # 다음 가져와야 할 timestamp 체크
        for_timestamp = timestamp + 1

        print(timestamp, " trading process start!! ")
        
        # Create Orders

        # index = 0       # 0: No position / 1: Bitmex short position / 2: Bitmex long position
        # arbitrage rate 계산
        ratio1 = round(exchanges['futures']['orderbook']['bids'][exchanges['futures']['bids_no']]["price"] / exchanges['spot']['orderbook']['asks'][exchanges['spot']['asks_no']]["price"], 8)
        ratio2 = round(exchanges['spot']['orderbook']['bids'][exchanges['spot']['bids_no']]["price"] / exchanges['futures']['orderbook']['asks'][exchanges['futures']['asks_no']]["price"], 8)

        print(ratio1, ratio2)

        # 
        if index == 0:
            if ratio1 > 1 + threshold:                
                if spot_usd_balance > unit * 2:
                    create_order(exchanges, futures_action='sell', spot_action='buy')
            elif ratio2 > 1 + threshold:                
                if spot_usd_balance > unit * 2:
                    create_order(exchanges, futures_action='buy', spot_action='sell')
            else:
                pass
        elif index == 1:
            if ratio1 > 1 + threshold:                
                if spot_usd_balance > unit * 2:
                    create_order(exchanges, futures_action='sell', spot_action='buy')
            elif ratio1 < 1:                
                if spot_usd_balance > unit * 2:
                    create_order(exchanges, futures_action='buy', spot_action='sell')
            else:
                pass
        elif index == 2:
            if ratio2 > 1 + threshold:                
                if spot_usd_balance > unit * 2:
                    create_order(exchanges, futures_action='buy', spot_action='sell')
            elif ratio2 < 1:                
                if spot_usd_balance > unit * 2:
                    create_order(exchanges, futures_action='sell', spot_action='buy')
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




def main(argv):
    FILE_NAME = argv[0]
    

    try:
        opts, etc_args = getopt.getopt(argv[1:], \
                                 "hf:s:y:", ["help","futures_name=","spot_name=","symbol="])
    
    except getopt.GetoptError: # 옵션지정이 올바르지 않은 경우
        print(FILE_NAME, '-f <futures_name> -s <spot_name> -y <symbol>')
        sys.exit(2)

    for opt, arg in opts: # 옵션이 파싱된 경우
        if opt in ("-h", "--help"): # HELP 요청인 경우 사용법 출력
            print(FILE_NAME, '-f <futures_name> -s <spot_name> -y <symbol>')
            sys.exit()

        elif opt in ("-f", "--futures_name"): # 선물 거래소 명 입력인 경우
            futures_name = arg
        elif opt in ("-s", "--spot_name"): # 현물 거래소 명 입력인 경우
            spot_name = arg
        elif opt in ("-y", "--symbol"): # thread 초 단위
            symbol = arg

    # if len(futures_name) < 1: # 필수항목 값이 비어있다면
    #     print(FILE_NAME, "-f 선물 거래소명을 반드시 입력 바랍니다.") # 필수임을 출력
    #     sys.exit(2)

    # if len(spot_name) < 1:
    #     print(FILE_NAME, "-s 현물 거래소명을 반드시 입력 바랍니다.") # 필수임을 출력
    #     sys.exit(2)

    # if len(symbol) < 1:
    #     symbol = 'BTC/USD'
    
    futures_name = 'bitmex'
    spot_name = 'bitstamp'
    symbol = 'BTC/USD'

    # if exchange_name == 'huobi':
    #     symbol = symbol.replace('/','-')
    
    # 여기서 부터 시작
    print('gogo')

    # arbitrage 대상 설정
    exchanges = {}    
    # 선물거래소
    obj = {}
    obj["exchange_name"] = futures_name
    obj["symbol"] = symbol    
    obj['type'] = 'futures'
    exchanges['futures'] = obj
    # 현물거래소
    obj = {}
    obj["exchange_name"] = spot_name
    obj["symbol"] = symbol    
    obj['type'] = 'spot'
    exchanges['spot'] = obj
    
    # 트레이딩 시작
    trading(exchanges)



# module이 아닌 main으로 실행된 경우 실행된다
if __name__ == "__main__":
    main(sys.argv)


