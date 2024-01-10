from sagemaker.feature_store.feature_group import FeatureGroup
import boto3
import pandas as pd
import numpy as np
import io
from sagemaker.session import Session
from sagemaker import get_execution_role

import hopsworks
import joblib

sagemaker_session = Session()

feature_group = FeatureGroup(name = 'BtcPriceData')

query = feature_group.athena_query()

table = query.table_name
table
default_s3_bucket_name = 'binance-btc-prices'
n_steps = 10

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


project = hopsworks.login()
mr = project.get_model_registry()
model = mr.get_model("lstmModel", version=3)
model_dir = model.download()

from tensorflow.keras.models import load_model
# Load the model
model = load_model(os.path.join(model_dir,'lstm_model.h5' ))


initial_sequence = np.array(dataset.close_price)

def predict_hours(initial_sequence, h = 6):
    recursive_preds = []
    initial_sequence = np.array(dataset.close_price)
    for i in range(h * 12):
        input_ = initial_sequence.reshape(1,10)
        pred = model.predict(input_,verbose = 0)[0][0]
        recursive_preds.append(pred)
        initial_sequence = np.append(initial_sequence,pred)[-10:]
    return recursive_preds

predict_hours(initial_sequence)