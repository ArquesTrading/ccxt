import datetime
import uuid
import urllib
import asyncio
import websockets
import json
import hmac
import base64
import hashlib
import gzip
import traceback
import zlib
import socket_data
import dbconnect as db


# okEx 의 Response Data 는 inflate 로 Decode 해야 한다.
def inflate(data):
    decompress = zlib.decompressobj(
            -zlib.MAX_WBITS  # see above
    )
    inflated = decompress.decompress(data)
    inflated += decompress.flush()
    return inflated     

def generate_signature(host, method, params, request_path, secret_key):
    """Generate signature of huobi future.
    
    Args:
        host: api domain url.PS: colo user should set this host as 'api.hbdm.com',not colo domain.
        method: request method.
        params: request params.
        request_path: "/notification"
        secret_key: api secret_key
    Returns:
        singature string.
    """
    host_url = urllib.parse.urlparse(host).hostname.lower()
    sorted_params = sorted(params.items(), key=lambda d: d[0], reverse=False)
    encode_params = urllib.parse.urlencode(sorted_params)
    payload = [method, host_url, request_path, encode_params]
    payload = "\n".join(payload)
    payload = payload.encode(encoding="UTF8")
    secret_key = secret_key.encode(encoding="utf8")
    digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(digest)
    signature = signature.decode()
    return signature

async def subscribe(exchange, url, access_key, secret_key, subs, callback=None, auth=False):
    """ Huobi Future subscribe websockets.
    Args:
        url: the url to be signatured.
        access_key: API access_key.
        secret_key: API secret_key.
        subs: the data list to subscribe.
        callback: the callback function to handle the ws data received. 
        auth: True: Need to be signatured. False: No need to be signatured.
    """
    async with websockets.connect(url) as websocket:
        if auth:
            # huobi 에서 작업된 버젼 , 다른 거래소는 확인해야함.
            timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
            data = {
                "AccessKeyId": access_key,
                "SignatureMethod": "HmacSHA256",
                "SignatureVersion": "2",
                "Timestamp": timestamp
            }
            sign = generate_signature(url,"GET", data, "/notification", secret_key)
            data["op"] = "auth"
            data["type"] = "api"
            data["Signature"] = sign
            msg_str = json.dumps(data)
            await websocket.send(msg_str)
            print(f"send: {msg_str}")
        # 여러개의 command 를 실행
        for sub in subs:
            sub_str = json.dumps(sub)
            await websocket.send(sub_str)
            print(f"send: {sub_str}")
        while True:
            data = await websocket.recv()  
                   
            try:
                data = json.loads(data)
            except UnicodeDecodeError as uni_decode:
                if exchange == 'okex':
                    data = inflate(data)
                    data = json.loads(data)
                else:
                    data = json.loads(gzip.decompress(data).decode())                        
            #print(f"recevie<--: {data}")

            if "op" in data and data.get("op") == "ping":
                pong_msg = {"op": "pong", "ts": data.get("ts")}
                await websocket.send(json.dumps(pong_msg))
                print(f"send: {pong_msg}")
                continue
            if "ping" in data: 
                pong_msg = {"pong": data.get("ping")}
                await websocket.send(json.dumps(pong_msg))
                print(f"send: {pong_msg}")
                continue
            rsp = await callback(exchange, data)

async def handle_ws_data(exchange, *args, **kwargs):
    """ callback function
    Args:
        args: values
        kwargs: key-values.
    """
    # print("callback param", *args,**kwargs)
    # rsp = *args
    # data = getattr(socket_data, 'bitmex')({
    #     'name': exchange,
    #     'data': rsp
    # })
    # data.datamining()
    
    l = list(args[0])
    data = args[0]

    # print(l)
    # print(data)

    
    if exchange == 'bitmex':
        if 'table' in data:
            data = getattr(socket_data, 'bitmex_data')({
                'name': 'bitmex',
                'data': data
            })
            dic = data.datamining()
            params = ("futures", "bitmex", "BTC/USD", json.dumps(dic))
            db.insert_order_book_rows(params)
    elif exchange == 'bitstamp':
        if l[0] == 'data':
            data = getattr(socket_data, 'bitstamp_data')({
                'name': 'bitstamp',
                'data': data
            })
            dic = data.datamining()
            # print(dic)
            params = ("spots", "bitstamp", "BTC/USD", json.dumps(dic))
            db.insert_order_book_rows(params)
    elif exchange == 'huobiswap':
        if 'tick' in data:
            data = getattr(socket_data, 'huobiswap_data')({
                'name': 'huobiswap',
                'data': data
            })
            dic = data.datamining()
            # print(dic)
            params = ("futures", "huobiswap", "BTC/USD", json.dumps(dic))
            db.insert_order_book_rows(params)
    elif exchange == 'okex':
        data = getattr(socket_data, 'okex_data')({
            'name': 'okex',
            'data': data
        })
        dic = data.datamining()
    else:
        print(*args)
                


def main(argv):
    FILE_NAME = argv[0]
    

    try:
        opts, etc_args = getopt.getopt(argv[1:], \
                                 "he:", ["help","exchange_name="])
    
    except getopt.GetoptError: # 옵션지정이 올바르지 않은 경우
        print(FILE_NAME, '-e <exchange name>')
        sys.exit(2)

    for opt, arg in opts: # 옵션이 파싱된 경우
        if opt in ("-h", "--help"): # HELP 요청인 경우 사용법 출력
            print(FILE_NAME, '-e <exchange name>')
            sys.exit()

        elif opt in ("-e", "--exchange"): # 거래소 명 입력인 경우
            exchange_name = arg
        
    if len(exchange_name) < 1: # 필수항목 값이 비어있다면
        print(FILE_NAME, "-e 거래소명은 반드시 입력 바랍니다. ( bitmex, coinbase )") # 필수임을 출력
        sys.exit(2)


    
    # exchange_name = 'bitmex'
    # symbol = 'XBTUSD'


    ####  input your access_key and secret_key below:

    # huobi api key info
    # access_key  = "02c0adfe-66883a97-qv2d5ctgbn-a1375"
    # secret_key  = "47a02bdc-d1d9966c-029c9ccb-24a13"
    access_key = ''
    secret_key = ''

    dic = {
        'bitmex':{
            'market_url': 'wss://www.bitmex.com/realtime?',
            'market_subs': [
                # bitmex request
                {
                    'op':'subscribe',
                    'args': ["orderBookL2_25:XBTUSD"]
                }
                # ,
                # {
                #     'op':'subscribe',
                #     'args': ['trade']
                # }
            ]
        },
        'bitstamp':{
            'market_url': 'wss://ws.bitstamp.net',
            'market_subs': [                
                # bitstamp request
                {
                    'event': 'bts:subscribe',
                    'data': {
                        'channel': 'order_book_btcusd'
                    }
                }                
            ]
        },
        'huobiswap':{
            'market_url': 'wss://api.hbdm.com/swap-ws',
            'market_subs': [                
                # huobi swap request
                {
                    "sub": "market.BTC-USD.depth.size_20.high_freq",
                    "id": str(uuid.uuid1())
                }  
            ]
        },
        'okex': {
            'market_url': 'wss://real.OKEx.com:8443/ws/v3',
            'market_subs': [
                {
                    'op':'subscribe',
                    'args': ['swap/depth:BTC-USD-SWAP']
                }
            ]
        },
        'bybit':{
            'market_url': 'wss://stream.bybit.com/realtime',
            'market_subs': [
                {
                    'op':'subscribe',
                    'args': ['orderBookL2_25.BTCUSD']
                }
            ]
        }
    }

    # order_subs = [
    #             {
    #                 "op": "sub",
    #                 "cid": str(uuid.uuid1()),
    #                 "topic": "orders.EOS"
    #             },
    #             {
    #                 "op": "sub",
    #                 "cid": str(uuid.uuid1()),
    #                 "topic": "positions.EOS"
    #             },
    #             {
    #                 "op": "sub",
    #                 "cid": str(uuid.uuid1()),
    #                 "topic": "accounts.EOS"
    #             }
    #         ]

    # exchange = 'huobiswap'

    market_url = dic[exchange]['market_url']
    market_subs = dic[exchange]['market_subs']

    while True: 
        try:
            asyncio.get_event_loop().run_until_complete(subscribe(exchange, market_url, access_key,  secret_key, market_subs, handle_ws_data, auth=False))
            #asyncio.get_event_loop().run_until_complete(subscribe(order_url, access_key,  secret_key, order_subs, handle_ws_data, auth=True))        
        except Exception as e:
            traceback.print_exc()
            print('websocket connection error. reconnect rightnow')

    


if __name__ == "__main__":
    main(sys.argv)    