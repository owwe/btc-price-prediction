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


# data "archive_file" "lambda" {
#   type        = "zip"
#   source_file = "daily_data_ingestor.py"
#   output_path = "data_ingestor.zip"
# }


resource "aws_lambda_function" "data-ingestor-lambda" {
  # If the file is not in the current working directory you will need to include a
  # path.module in the filename.
  image_uri      = "477472432946.dkr.ecr.eu-north-1.amazonaws.com/daily-data-ingestor-lambda-image:latest"
  function_name = "btc_feature_store_data_ingestor"
  role          = aws_iam_role.iam_for_data_ingestor_lambda.arn
  package_type  = "Image"
  #source_code_hash = data.archive_file.lambda.output_base64sha256

}

resource "aws_scheduler_schedule" "btc-data-ingestor-sch" {
  name       = "btc-price-ingestor-sch"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(0 0/2 * * ? 2024)"  # Run every 2 hours starting from 2024-01-09 00:00

  schedule_expression_timezone = "UTC"
  start_date = "2024-01-09T01:55:55Z"
   
   target {
    arn      = aws_lambda_function.data-ingestor-lambda.arn  # Use the Lambda function ARN
    role_arn = aws_iam_role.iam_for_data_ingestor_lambda.arn
    }
}