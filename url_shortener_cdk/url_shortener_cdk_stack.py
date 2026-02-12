from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cf,
    aws_cloudfront_origins as origins,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct

class UrlShortenerCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ────────────────────────────────────────────────
        # API Gateway and Lambdas
        # ────────────────────────────────────────────────

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

        # ────────────────────────────────────────────────
        # Frontend: S3 Bucket + Deployment + CloudFront
        # ────────────────────────────────────────────────

        # S3 Bucket for static files (not public directly)
        frontend_bucket = s3.Bucket(
            self,
            "FrontendBucket",
            bucket_name=f"url-shortener-frontend-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
        )

        # CloudFront Distribution (HTTPS, caching, serves from S3)
        distribution = cf.Distribution(
            self,
            "FrontendDistribution",
            default_behavior=cf.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(frontend_bucket),
                viewer_protocol_policy=cf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cf.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cached_methods=cf.CachedMethods.CACHE_GET_HEAD_OPTIONS,
                cache_policy=cf.CachePolicy.CACHING_OPTIMIZED,
            ),
            default_root_object="index.html",
            error_responses=[
                cf.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                ),
                cf.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                ),
            ],
        )

        # Deploy frontend build output (run: cd frontend && npm run build first)
        s3deploy.BucketDeployment(
            self,
            "DeployFrontend",
            sources=[s3deploy.Source.asset("./frontend/dist")],
            destination_bucket=frontend_bucket,
            destination_key_prefix="",
            retain_on_delete=False,
            distribution=distribution,
            distribution_paths=["/*"],
        )

        frontend_domain = distribution.distribution_domain_name
        frontend_origin = f"https://{frontend_domain}"

        # ────────────────────────────────────────────────
        # API Gateway
        # ────────────────────────────────────────────────

        allowed_origins = self.node.try_get_context("allowed_origins") or [
            "http://localhost:5173",
            "http://localhost:3000",
        ]

        api = apigw.RestApi(
            self, "UrlShortenerApi",
            deploy_options=apigw.StageOptions(stage_name="prod"),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=allowed_origins,
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["Content-Type", "Authorization"],
            ),
        )

        # /urls POST
        urls = api.root.add_resource("urls")
        urls.add_method(
            "POST",
            apigw.LambdaIntegration(shorten_lambda),
        )

        # /r/{short_code} GET
        r = api.root.add_resource("r")
        short = r.add_resource("{short_code}")
        short.add_method(
            "GET",
            apigw.LambdaIntegration(redirect_lambda),
        )

        api_origin = origins.HttpOrigin(
            f"{api.rest_api_id}.execute-api.{self.region}.amazonaws.com",
            origin_path=f"/{api.deployment_stage.stage_name}",
        )

        distribution.add_behavior(
            "/urls*",
            api_origin,
            allowed_methods=cf.AllowedMethods.ALLOW_ALL,
            cache_policy=cf.CachePolicy.CACHING_DISABLED,
        )

        distribution.add_behavior(
            "/r/*",
            api_origin,
            allowed_methods=cf.AllowedMethods.ALLOW_ALL,
            cache_policy=cf.CachePolicy.CACHING_DISABLED,
        )


        # Outputs
        CfnOutput(self, "ApiEndpoint", value=api.url)
        CfnOutput(self, "FrontendURL", value=frontend_origin)


