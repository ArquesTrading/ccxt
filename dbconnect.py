import  pyodbc

server = 'arquestrade.database.windows.net'
database = 'ArquesTradingDB'
username = 'arques_admin'
password = 'Password!1234'
driver = '{ODBC Driver 17 for SQL Server}'
#cnxn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';PORT=1433;DATABASE=' + database + ';UID=' + username + ';PWD=' + password + ';')


def connect():
    connection_string = 'DRIVER=' + driver + ';SERVER=' + server + ';PORT=1433;DATABASE=' + database + ';UID=' + username + ';PWD=' + password + ';'
    return pyodbc.connect(connection_string)

def run_query(query):
    with connect() as cnxn:
        cursor = cnxn.cursor()
        cursor.execute(query)        
        row = cursor.fetchall()

    return row

def exec_sp(query, params):
    with connect() as cnxn:
        cursor = cnxn.cursor()
        cursor.execute(query, params)        
        row = cursor.fetchall()

    return row

def exec_sp_nonquery(query, params):
    with connect() as cnxn:
        cursor = cnxn.cursor()
        cursor.execute(query, params)        
        row = cursor.fetchone()

    return row


def insert_price(exchange_name, params):
    query = """\
    DECLARE @v_sp_rtn   INT

    EXEC    dbo.SP_T_CRYPTO_PRICE_INFO_C
            @i_exchange_name    = ?
        ,   @i_symbol           = ?
        ,   @i_period           = ?
        ,   @i_timestamp		= ?
        ,	@i_log_time			= ?
        ,	@i_open				= ?
        ,	@i_high				= ?
        ,	@i_low				= ?
        ,	@i_close			= ?
        ,	@i_volume			= ?
        ,   @o_sp_rtn           = @v_sp_rtn OUTPUT;

    SELECT  @v_sp_rtn as out

    """
    with connect() as cnxn:
        cursor = cnxn.cursor()
        cursor.execute(query, params)        
        row = cursor.fetchone()

    return row

def insert_order_book(params):
    query = """\
    DECLARE @v_sp_rtn   INT

    EXEC    dbo.SP_T_CRYPTO_ORDER_BOOK_INFO_C
            @i_exchange_name    = ?
        ,   @i_symbol           = ?        
        ,   @i_timestamp		= ?
        ,	@i_log_time			= ?
        ,   @i_kind             = ?
        ,   @i_idx              = ?
        ,	@i_price			= ?
        ,	@i_volume			= ?
        ,   @o_sp_rtn           = @v_sp_rtn OUTPUT;

    SELECT  @v_sp_rtn as out
   
    """
    with connect() as cnxn:
        cursor = cnxn.cursor()
        cursor.execute(query, params)        
        row = cursor.fetchone()

    return row

def insert_trading_log(params):
    query = """\
    DECLARE @v_sp_rtn   INT

    EXEC    dbo.SP_T_CRYPTO_TRADING_LOG_C
            @i_timestamp			= ?
        ,	@i_trading_name			= ?
        ,	@i_index				= ?
        ,	@i_ratio1				= ?
        ,	@i_ratio2				= ?
        ,	@i_comment				= ?
        ,	@i_order_description	= ?
        ,	@o_sp_rtn				= @v_sp_rtn OUTPUT;

    SELECT  @v_sp_rtn as out
    """
    with connect() as cnxn:
        cursor = cnxn.cursor()
        cursor.execute(query, params)        
        row = cursor.fetchone()

    return row

def insert_trading_log_v2(params):
    query = """\
    DECLARE @v_sp_rtn   INT
    EXEC    dbo.SP_T_CRYPTO_TRADING_LOG_v2_C
    	@i_trading_name			= ?
    ,	@i_timestamp			= ?
    ,	@i_step					= ?
    ,   @i_threshold			= ?
    ,	@i_fees					= ?
    ,   @i_futures_btc_balance  = ?
    ,   @i_futures_usd_balance  = ?
    ,   @i_spots_btc_balance    = ?
    ,   @i_spots_usd_balance    = ?
    ,	@i_futures_exchange		= ?
    ,	@i_futures_action		= ?
    ,	@i_futures_price		= ?
    ,	@i_futures_amount		= ?
    ,	@i_spots_exchange		= ?
    ,	@i_spots_action			= ?
    ,	@i_spots_price			= ?
    ,	@i_spots_amount			= ?
    ,	@i_from_index			= ?
    ,	@i_to_index				= ?
    ,	@i_ratio1				= ?
    ,	@i_ratio2				= ?
    ,	@i_unit					= ?
    ,	@i_unit_satoshi			= ?
    ,	@i_bitmex_bids_no		= ?
    ,	@i_bitmex_asks_no		= ?
    ,	@i_bitstamp_bids_no		= ?
    ,	@i_bitstamp_asks_no		= ?
    ,	@i_comment				= ?
    ,   @i_bitmex_size          = ?
    ,	@o_sp_rtn				= @v_sp_rtn	OUTPUT;

    SELECT  @v_sp_rtn as out
    """
    with connect() as cnxn:
        cursor = cnxn.cursor()
        cursor.execute(query, params)        
        row = cursor.fetchone()

    return row

def insert_order_book_rows(params):    
    query = """\
    DECLARE @v_sp_rtn   INT

    EXEC    dbo.SP_T_CRYPTO_ORDER_BOOK_INFO_REALTIME_C
            @i_exchange_type    = ?
        ,   @i_exchange_name    = ?
        ,   @i_symbol           = ?        
        ,   @i_json             = ?
        ,   @o_sp_rtn           = @v_sp_rtn OUTPUT;

    SELECT  @v_sp_rtn as out
   
    """
    with connect() as cnxn:
        cursor = cnxn.cursor()
        cursor.execute(query, params)        
        row = cursor.fetchone()

    return row


