FROM public.ecr.aws/lambda/python:3.10

# Copy your Lambda function code
COPY lambda-requirements.txt ${LAMBDA_TASK_ROOT}
COPY daily_data_ingestor.py ${LAMBDA_TASK_ROOT}

#RUN pip install -r requirements.txt
RUN pip install -r ${LAMBDA_TASK_ROOT}/lambda-requirements.txt

# Set the CMD to your handler (adjust based on your function)
CMD [ "daily_data_ingestor.handler" ]



