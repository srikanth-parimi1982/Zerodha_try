# Algo Trading with Himmat
    # Strategy  - RSI
    # Entry     - RSI Above 60 / RSI Below 40
    # Exit      - Set defined Stop Loss or Target

import datetime as dt
import pandas as pd
import time
import talib

from configparser import ConfigParser
from kiteconnect import KiteConnect
# read config.ini
config          = ConfigParser()
config.read('config.ini')
# Zerodha_APP details section
api_key         = config.get('Zerodha_APP', 'api_Key')
api_secret      = config.get('Zerodha_APP', 'api_secret')
kite            = KiteConnect(api_key=api_key)
# print(kite.login_url()) # https://kite.zerodha.com/connect/login?api_key=*********&v=3
data            = kite.generate_session("erKTxgzTAUWlonoEUA1uuuE10f7gFGji", api_secret=api_secret)
access_token    = data["access_token"]
kite.set_access_token(access_token)

# initialize variables
is_long_trade       = False
is_short_trade      = False
rsi_period          = 14
call_rsi_threshold  = 60
put_rsi_threshold   = 40
option_symbol       = 'BANKNIFTY24131'
trade_quantity      = 15

def placeOrder(symbol,BorS):
	orderId = kite.place_order(
            variety='regular',
            exchange='NFO',
            tradingsymbol=symbol,
            transaction_type=BorS,
            quantity=trade_quantity,
            product='NRML',
            order_type='MARKET',
            validity='DAY'
        )
	print('Order Placed :: '+str(symbol)+' Transaction :: '+str(BorS)+' Id :: '+str(orderId))
	return orderId

def process_data(data):
    global is_long_trade, is_short_trade
    
    df                  = pd.DataFrame(data)
    df['rsi']           = talib.RSI(df['close'], timeperiod=rsi_period)

    print(str(time.localtime().tm_hour)+':'+str(time.localtime().tm_min)+':'+str(time.localtime().tm_sec)+\
          " RSI (-2 Candle) : "+str(df['rsi'].iloc[-2])+" RSI (-1 Candle) : "+str(df['rsi'].iloc[-1]))

    # Check for long entry condition
    if not is_long_trade and df['rsi'].iloc[-2] < call_rsi_threshold and df['rsi'].iloc[-1] > call_rsi_threshold:
        print("Call Buy Entry : ")
        round_to_strike     = int(round(float(df['close'].iloc[-1]), -2)) # round closed price to nearest strike price
        call_symbol         = str(option_symbol)+str(round_to_strike)+'CE'
        orderId             = placeOrder(call_symbol, 'BUY')
        is_long_trade       = True

    # Check for short entry condition
    if not is_short_trade and df['rsi'].iloc[-2] > put_rsi_threshold and df['rsi'].iloc[-1] < put_rsi_threshold:
        print("Put Buy Entry : ")
        round_to_strike = int(round(float(df['close'].iloc[-1]), -2)) # round closed price to nearest strike price
        put_symbol      = str(option_symbol)+str(round_to_strike)+'PE'
        orderId         = placeOrder(put_symbol, 'BUY')
        is_short_trade  = True

    #if is_long_trade:
         # logic to exit call

    #if is_short_trade:
         # logic to exit put 

# Get Bank Nifty Instrument Token to Fetch Historical Data
banknifty_symbol    = 'NSE:NIFTY BANK'
instruments         = kite.instruments('NSE')
instrumentsDf       = pd.DataFrame(instruments)
indicesDf           = instrumentsDf[instrumentsDf['segment'] == 'INDICES']
bankNiftyDf         = indicesDf[indicesDf['name'] == 'NIFTY BANK']
BNInstrumentToken   = bankNiftyDf['instrument_token'].iloc[0]

while True:
    to_date         = dt.datetime.now().date()
    from_date       = to_date - dt.timedelta(days = 5)
    historicData    = kite.historical_data(instrument_token=BNInstrumentToken, from_date=from_date, to_date=to_date, interval='5minute')
    process_data(historicData)
    time.sleep(300) # sleep for 5 minute until next candle formed
