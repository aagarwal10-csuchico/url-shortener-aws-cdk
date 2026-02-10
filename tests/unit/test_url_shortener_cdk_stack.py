from aws_cdk import App
from aws_cdk.assertions import Template

from url_shortener_cdk.url_shortener_cdk_stack import UrlShortenerCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in url_shortener_cdk/url_shortener_cdk_stack.py
def test_stack():
    app = App()
    stack = UrlShortenerCdkStack(app, "url-shortener-cdk")
    template = Template.from_stack(stack)
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "BillingMode": "PAY_PER_REQUEST"
    })
    template.resource_count_is("AWS::Lambda::Function", 2)
