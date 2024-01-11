from binance.spot import Spot
from datetime import datetime,timedelta
from sagemaker.feature_store.feature_group import FeatureGroup
import boto3
import pandas as pd
import numpy as np
import io
import json
import hopsworks
import os

def handler(event,context):
    feature_group = FeatureGroup(name = 'BtcPriceData')
    client = Spot()
    klines = client.klines("BTCUSDT", "5m",limit = 4*12)
    df = pd.DataFrame(klines, columns =['open_time','open_price','high_price','low_price',
                                        'close_price','volume','close_time','quote_asset_volume',
                                        'number_of_trades','taker_buy_base_asset_volume',
                                         'taker_buy_quote_asset_volume','ignore'])
    
    df['close_time'] =  df['close_time'].div(1000)
    df = df.drop(columns = ['ignore','taker_buy_quote_asset_volume'])
    df = df.astype(float)
    #print(df)
    #feature_group.load_feature_definitions(df)
    feature_group.ingest(data_frame=df, wait=True)

    if datetime.now().hour == 0 or datetime.now().hour == 4:
        project = hopsworks.login(api_key_value= os.environ['HOPSWORKS_API_KEY'], project="project0")
        fs = project.get_feature_store()
        klines = client.klines("BTCUSDT", "1d",limit = 1)
        df = pd.DataFrame(klines, columns =["Open time","Open","High","Low",
                                            "Close","Volume","Close time",
                                            "Quote asset volume","Number of trades",
                                            "Taker buy base asset volume",
                                            "Taker buy quote asset volume",
                                            "Ignore"])
        
        df['close_time'] =  df['close_time'].div(1000)
        df['close_time'] =  df['close_time'].div(1000)
        df = df.astype(float)
        df["Open time"] = pd.to_datetime(df["Open time"], unit="s")
        df["Close time"] = pd.to_datetime(df["Close time"], unit="s")
        df = df.drop('Ignore', axis=1)

        df.columns = df.columns.str.lower().str.replace(' ', '_')

        btc_fg = fs.get_feature_group(name="btc",version=1)
        btc_fg.insert(df)
    return "200"
