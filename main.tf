provider "aws" {
  region = "eu-north-1"  # Set your desired AWS region
}


data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com",
                     "scheduler.amazonaws.com"   ]
    }

    actions = ["sts:AssumeRole"]
  }
}


resource "aws_iam_role" "iam_for_data_ingestor_lambda" {
  name               = "iam_for_data_ingestor_lambda"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}




resource "aws_s3_bucket" "btc-lambda-fn" {
  bucket = "btc-ingestor-lambda-fn-bucket"

  tags = {
    Name        = "btc-ingestor-lambda-fn"
    Environment = "Dev"
  }
}

data "archive_file" "lambda" {
  type        = "zip"
  source_file = "lambda_btc_price_ingestor"
  output_path = "daily_data_ingestor.zip"
}

resource "aws_s3_bucket_object" "lambda_object" {
  bucket = aws_s3_bucket.btc-lambda-fn.bucket
  key    = "daily_data_ingestor.zip"
  source = data.archive_file.lambda.output_path
  acl    = "private"
}


resource "aws_lambda_function" "data-ingestor-lambda-fn" {
  # If the file is not in the current working directory you will need to include a
  # path.module in the filename.
  filename =  aws_s3_bucket_object.lambda_object.bucket
  #image_uri     = "477472432946.dkr.ecr.eu-north-1.amazonaws.com/daily-data-ingestor-lambda-image:latest"
  function_name = "btc_feature_store_data_ingestor"
  role          = aws_iam_role.iam_for_data_ingestor_lambda.arn
  package_type  = "Image"
  timeout       = 800
  memory_size = 512
  #source_code_hash = data.archive_file.lambda.output_base64sha256

}

resource "aws_scheduler_schedule" "btc-data-ingestor-sch" {
  name       = "btc-price-ingestor-sch"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(0 0/4 * * ? 2024)"  # Run every 2 hours starting from 2024-01-09 00:00

  schedule_expression_timezone = "UTC"
  start_date = "2024-01-09T12:55:55Z"
   
   target {
    arn      = aws_lambda_function.data-ingestor-lambda.arn  # Use the Lambda function ARN
    role_arn = aws_iam_role.iam_for_data_ingestor_lambda.arn
    }
}