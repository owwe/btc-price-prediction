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
    klines = client.klines("BTCUSDT", "5m",limit = 1*12)
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

    return "200"
