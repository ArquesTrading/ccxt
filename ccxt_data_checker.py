import pyodbc
import dbconnect as db
import tablib

def get_data_grouping(symbol, period):
    query = """\
    DECLARE @v_sp_rtn   INT

    EXEC    dbo.SP_T_CRYPTO_GROUP_MONITORING_R
            @i_symbol           = ?
        ,   @i_period           = ?
        ,   @o_sp_rtn           = @v_sp_rtn OUTPUT;

    SELECT  @v_sp_rtn as out

    """

    params = (symbol, period)

    with db.connect() as cnxn:
        cursor = cnxn.cursor()
        cursor.execute(query, params)        
        row = cursor.fetchall()

        idx = 0

        data = []
        column = []
        result = 0
        while row:
            
            if idx == 0:
                data = row
                # for r in row:
                #     print (r)
            elif idx == 1:
                for r in row:
                    # print (r)
                    column = r[0].split(',')
            else:
                # print(row)
                result = row[0][0]
            
            if cursor.nextset():
                row = cursor.fetchall()
            else:
                row = None

            idx +=1
        
        # print(result)
        # print(column)
        # print(data)
        if result == 0:
            table = tablib.Dataset(*data, headers=column)
            print(table)
            print(type(table))
            
        else:
            print('NO DATA')


def get_data_price(exchange_name, symbol, period=None, timestamp=None, log_time=None, page_size=None):
    query = """\
         DECLARE @v_sp_rtn   INT

        EXEC    dbo.SP_T_CRYPTO_PRICE_INFO_R
                @i_exchange_name	= ?
            ,	@i_symbol			= ?
            ,	@i_period			= ?
            ,	@i_timestamp		= ?
            ,	@i_log_time			= ?
            ,	@i_page_size		= ?
            ,	@o_sp_rtn			= @v_sp_rtn	OUTPUT;

        SELECT  @v_sp_rtn as out

        """

    params = (exchange_name, symbol, period, timestamp, log_time, page_size)

    with db.connect() as cnxn:
        cursor = cnxn.cursor()
        cursor.execute(query, params)        
        row = cursor.fetchall()

        idx = 0

        data = []
        column = ['exchange_name', 'symbol', 'period', 'timestamp', 'datetime', 'open', 'high', 'low', 'close', 'volumn']
        result = 0
        while row:
            
            if idx == 0:
                data = row
                # for r in row:
                #     print (r)            
            else:
                # print(row)
                result = row[0][0]
            
            if cursor.nextset():
                row = cursor.fetchall()
            else:
                row = None

            idx +=1
        
        # print(result)
        # print(column)
        # print(data)
        if result == 0:
            table = tablib.Dataset(*data, headers=column)
            print(table)
            print(type(table))
            
        else:
            print('NO DATA')

        

# get_data_grouping('BTC/USD', '1m')
# get_data_grouping('BTC/USD', 'tick')
# get_data_price('bitmex', 'BTC/USD', None, None, None, None)
get_data_price('bitmex', 'BTC/USD', '1m', 1589242740000, '2020-05-12', 20)


