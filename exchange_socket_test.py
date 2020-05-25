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
                if exchange == 'ok':
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
            rsp = await callback(data)

async def handle_ws_data(*args, **kwargs):
    """ callback function
    Args:
        args: values
        kwargs: key-values.
    """
    # print("callback param", *args,**kwargs)
    print(*args)

if __name__ == "__main__":
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
                },
                {
                    'op':'subscribe',
                    'args': ['trade']
                }
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
                    'args': ['swap/depth5:BTC-USD-SWAP']
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

    exchange = 'bitmex'

    market_url = dic[exchange]['market_url']
    market_subs = dic[exchange]['market_subs']

    while True: 
        try:
            asyncio.get_event_loop().run_until_complete(subscribe(exchange, market_url, access_key,  secret_key, market_subs, handle_ws_data, auth=False))
            #asyncio.get_event_loop().run_until_complete(subscribe(order_url, access_key,  secret_key, order_subs, handle_ws_data, auth=True))        
        except Exception as e:
            traceback.print_exc()
            print('websocket connection error. reconnect rightnow')