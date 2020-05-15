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







