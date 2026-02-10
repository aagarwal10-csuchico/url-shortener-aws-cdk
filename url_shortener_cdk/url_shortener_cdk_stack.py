from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct

class UrlShortenerCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # DynamoDB Tables
        mappings_table = dynamodb.Table(
            self, "UrlMappings",
            partition_key={"name": "short_code", "type": dynamodb.AttributeType.STRING},
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute="expiration_time",
        )

        counters_table = dynamodb.Table(
            self, "Counters",
            partition_key={"name": "counter_id", "type": dynamodb.AttributeType.STRING},
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Lambdas
        shorten_lambda = _lambda.Function(
            self, "ShortenUrl",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("lambdas/shorten"),
            environment={
                "MAPPINGS_TABLE": mappings_table.table_name,
                "COUNTERS_TABLE": counters_table.table_name,
            },
        )

        redirect_lambda = _lambda.Function(
            self, "RedirectUrl",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("lambdas/redirect"),
            environment={
                "MAPPINGS_TABLE": mappings_table.table_name,
                "COUNTERS_TABLE": counters_table.table_name,
            },
        )

        # Grant permissions
        mappings_table.grant_read_write_data(shorten_lambda)
        mappings_table.grant_read_data(redirect_lambda)
        counters_table.grant_write_data(shorten_lambda)

        # API Gateway
        api = apigw.RestApi(
            self, "UrlShortenerApi",
            deploy_options=apigw.StageOptions(stage_name="prod"),
        )

        # /urls POST
        urls = api.root.add_resource("urls")
        urls.add_method(
            "POST",
            apigw.LambdaIntegration(shorten_lambda),
        )

        # /{short_code} GET
        short = api.root.add_resource("{short_code}")
        short.add_method(
            "GET",
            apigw.LambdaIntegration(redirect_lambda),
        )

        # Outputs
        CfnOutput(self, "ApiEndpoint", value=api.url)


