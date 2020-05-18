
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

def get_data():    

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
        
        


while True:
    data = get_data()

    print(data)

    time.sleep(0.5)