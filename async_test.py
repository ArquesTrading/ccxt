import asyncio
import ccxt.async_support as ccxt


async def async_client(exchange_name, symbol):
    if exchange_name == 'coinbase':
        exchange_name = 'coinbasepro'
      
    client = getattr(ccxt, exchange_name)()
    ticker = await client.fetch_ticker(symbol)
    await client.close()
    return ticker

async def multi_ticker():
    while True:
        exchanges = ["bitmex", "coinbase", "bitstamp"]
        symbol = "BTC/USD"
        input_tickers = [async_client(exchange_name, symbol) for exchange_name in exchanges]
        tickers = await asyncio.gather(*input_tickers, return_exceptions=True)

        print(tickers)
        # print('aaa')
        await asyncio.sleep(1)


async def periodic():
    while True:
        print('periodic')
        await asyncio.sleep(1)


def stop():
    task.cancel()


loop = asyncio.get_event_loop()
loop.call_later(10, stop)
task = loop.create_task(multi_ticker())

try:
    loop.run_until_complete(task)
except asyncio.CancelledError:
    pass