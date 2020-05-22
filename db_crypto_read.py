
import os
import sys
import time
import dbconnect as db

# -----------------------------------------------------------------------------
# DB 에 쌓인 데이터 조회
# -----------------------------------------------------------------------------

def get_dic(column, row):
    dic = {}
    idx = 0
    for i in column:
        # print(i)
        # print(row[0][idx])
        dic[i] = row[0][idx]
        idx = idx + 1

    return dic

def get_order_book_dic(row):
    dic = {}

    bids = []
    asks = []
    obj = {}

    # print(len(row))

    for i in range(len(row)):
        r = row[i]

        # print(r)

        if i == 0:
            dic["exchange_name"] = r[0]
            dic["symbol"] = r[1]
            dic["timestamp"] = r[2]
            dic["log_time"] = r[3]

        if r[4] == "asks":
            obj = {}
            obj["idx"] = r[5]
            obj["price"] = r[6]
            obj["volume"] = r[7]
            asks.append(obj)            
        elif r[4] == "bids":
            obj = {}
            obj["idx"] = r[5]
            obj["price"] = r[6]
            obj["volume"] = r[7]
            bids.append(obj)

    dic["bids"] = bids
    dic["asks"] = asks

    return dic


def get_price_data():    

    query = """\
        DECLARE @v_sp_rtn   INT

        EXEC    dbo.SP_T_CRYPTO_PRICE_INFO_R
                @o_sp_rtn			= @v_sp_rtn	OUTPUT;

        SELECT  @v_sp_rtn as out

        """
    params = {}
    with db.connect() as cnxn:
        cursor = cnxn.cursor()
        cursor.execute(query)        
        row = cursor.fetchall()

        idx = 0

        data = []    
        column = ['min_timestamp', 'max_timestamp', 'min_log_time', 'max_log_time', 'second_diff', 'bitmex', 'coinbase', 'bitstamp', 'huobi', 'okex']    
        result = 0
        while row:
            
            if idx == 0:
                data = get_dic(column, row)
            else:                    
                result = row[0][0]
            
            if cursor.nextset():
                row = cursor.fetchall()
            else:
                row = None

            idx +=1
        
        if result == 0:
            # print(column)
            return data          
        else:
            return None

def get_order_book_data(exchange_name, symbol, timestamp=None):
    query = """\
        DECLARE @v_sp_rtn   INT

        EXEC    dbo.SP_T_CRYPTO_ORDER_BOOK_INFO_FILTER_R
                @i_exchange_name    = ?
            ,   @i_symbol           = ?
            ,   @i_timestamp        = ?
            ,   @o_sp_rtn			= @v_sp_rtn	OUTPUT;

        SELECT  @v_sp_rtn as out

        """
    params = (exchange_name, symbol, timestamp)
    # print(query, params)
    with db.connect() as cnxn:
        cursor = cnxn.cursor()
        cursor.execute(query, params)        
        row = cursor.fetchall()

        idx = 0

        data = []            
        result = 0
        while row:
            
            if idx == 0:
                data = get_order_book_dic(row)
            else:  
                # print(row[0][0])                  
                result = row[0][0]
            
            if cursor.nextset():
                row = cursor.fetchall()
            else:
                row = None

            idx +=1
        
        if result == 0:
            # print(column)
            return data          
        else:
            time.sleep(3)
            return get_order_book_data(exchange_name, symbol, timestamp)
        


# while True:
#     data = get_price_data()
#     print(data)

#     order_book = get_order_book_data('bitmex', 'BTC/USD', 1589862151591)
#     print(order_book)

#     time.sleep(1)