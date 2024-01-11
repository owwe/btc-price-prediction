FROM public.ecr.aws/lambda/python:3.10

# Copy your Lambda function code
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY src/* ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (adjust based on your function)
CMD [ "main.handler" ]


