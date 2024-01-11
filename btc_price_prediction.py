from sagemaker.feature_store.feature_group import FeatureGroup
import boto3
import pandas as pd
import numpy as np
import io
from sagemaker.session import Session
from sagemaker import get_execution_role
import matplotlib.pyplot as plt



def predict_hours(model,initial_sequence, h = 6):
    recursive_preds = []
    for i in range(h * 12):
        input_ = initial_sequence.reshape(1,n_steps)
        pred = model.predict(input_,verbose = 0)[0][0]
        recursive_preds.append(pred)
        initial_sequence = np.append(initial_sequence,pred)[-n_steps:]
    return recursive_preds

def main():
    sagemaker_session = Session()

    feature_group = FeatureGroup(name = 'BtcPriceData')

    query = feature_group.athena_query()

    table = query.table_name
    table
    default_s3_bucket_name = 'binance-btc-prices'
    n_steps = 50

    q= f'''
    SELECT *
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

    # run Athena query. The output is loaded to a Pandas dataframe.
    dataset = pd.DataFrame()
    query.run(query_string=q, output_location='s3://'+default_s3_bucket_name+'/query_results/')
    query.wait()
    dataset = query.as_dataframe()

    import hopsworks
    import joblib
    project = hopsworks.login()


    mr = project.get_model_registry()
    model = mr.get_model("mlpModel", version=1)
    model_dir = model.download()

    from tensorflow.keras.models import load_model
    # Load the model
    model = load_model(os.path.join(model_dir,'mlp.h5' ))

    initial_sequence = np.array(dataset.close_price)
    preds = predict_hours(model, initial_sequence, h = 24)





