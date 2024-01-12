from sagemaker.feature_store.feature_group import FeatureGroup
import boto3
import pandas as pd
import numpy as np
from sagemaker.session import Session
from sagemaker import get_execution_role
import os
from tensorflow.keras.models import load_model
from datetime import datetime, timedelta
import hopsworks
from dotenv import load_dotenv

def predict_hours(model,initial_sequence, h = 6):
    recursive_preds = []
    for i in range(h * 12):
        input_ = initial_sequence.reshape(1,n_steps)
        pred = model.predict(input_,verbose = 0)[0][0]
        recursive_preds.append(pred)
        initial_sequence = np.append(initial_sequence,pred)[-n_steps:]
        #print(initial_sequence)
    return recursive_preds
def handler(event, context):

    sagemaker_session = Session()

    feature_group = FeatureGroup(name = 'BtcPriceData')

    query = feature_group.athena_query()

    table = query.table_name
    table
    default_s3_bucket_name = 'binance-btc-prices'
    n_steps = 24

    q= f'''
    SELECT "open_time","close_price"
    FROM
        (SELECT *,
        row_number()
        OVER
            (PARTITION BY "open_time"
            ORDER BY "close_time" DESC, Api_Invocation_Time DESC, write_time DESC)
        AS row_number
        FROM "sagemaker_featurestore"."btcpricedata_1704246894")
    WHERE row_number = 1 ORDER BY close_time desc limit {n_steps};
    '''

    dataset = pd.DataFrame()
    query.run(query_string=q, output_location='s3://'+default_s3_bucket_name+'/query_results/')
    query.wait()
    dataset = query.as_dataframe()


    load_dotenv()
    project = hopsworks.login(project ='DD2223_lab1' , api_key_value  = os.getenv("HOPSWORKS_API_KEY"))

    mr = project.get_model_registry()
    model = mr.get_model("mlpModel", version=2)
    model_dir = model.download()

    # Load the model
    model = load_model(os.path.join(model_dir,'mlp.keras' ))#+ '/lstm_model.h5'))
    print('model is loaded',model.summary())

    initial_sequence = np.array(dataset.close_price)[::-1]
    print(initial_sequence)
    preds = predict_hours(model, initial_sequence, h = 1)
    print(preds)


    dates = [ int((pd.to_datetime(dataset['open_time'][0],unit = 'ms') + timedelta(minutes = 5 * i)).timestamp() * 1000) for i in range(1,13)]
    df = pd.DataFrame(data = {'price_predictions':preds,'timestamp':dates})
    print(df.head())
    feature_group = FeatureGroup(name = 'btc-price-predictions')
    feature_group.ingest(data_frame=df, max_workers=1, wait=True)