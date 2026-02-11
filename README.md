
# Serverless URL Shortener

A production-ready, serverless URL shortening service built with **AWS CDK (Python)**, **AWS Lambda**, **Amazon API Gateway**, and **Amazon DynamoDB**.

This project implements a simple yet scalable URL shortener **backend** — perfect for learning serverless architecture, infrastructure as code (IaC), and DynamoDB modeling patterns.

**Currently implemented:**
- Infrastructure as Code with AWS CDK (Python)
- Two DynamoDB tables for URL mappings and atomic counter
- Lambda functions for shortening URLs and handling redirects
- API Gateway REST API with `/shorten` and `/{short_code}` endpoints
- Automatic IAM permissions and resource configuration

**Future work:**
- Modern web frontend
- Custom domain with HTTPS

## Features (Backend)

- Shorten any long URL → returns a short code (e.g. `abc123`)
- Redirect from short URL → 301 permanent redirect to the original URL
- Atomic counter stored in DynamoDB to generate unique short codes
- Base62 encoding for short, readable codes
- Collision-resistant short code generation
- Fully serverless — zero servers to manage, pay-per-use pricing
- Entire infrastructure defined and deployable with a single `cdk deploy`

## Architecture

```text
             ┌───────────────────────┐
             │      API Gateway      │
             │       (REST API)      │
             └───────────┬───────────┘
                         │
      ┌──────────────────┼─────────────────┐
      │                  │                 │
┌────────────┐                      ┌────────────┐
│  shorten   │                      │  redirect  │
│   Lambda   │                      │   Lambda   │
└──────┬─────┘                      └──────┬─────┘
       │                                   │
       └─────────────────┼─────────────────┘
                         │
                ┌─────────────────┐
                │                 │
                │     DynamoDB    │
                │  - UrlMappings  │
                │  - Counters     │
                └─────────────────┘
```


## Tech Stack

- **AWS CDK** (v2) – Python
- **AWS Lambda** – Python 3.12 runtime
- **Amazon API Gateway** – REST API
- **Amazon DynamoDB** – two tables:
  - `UrlMappings` – partition key: `short_code` (string)
  - `Counters` – partition key: `counter_id` (string)
- **boto3** – AWS SDK for Python

## Prerequisites

- Python 3.10+
- AWS CLI configured (`aws configure`)
- Node.js (required by CDK)
- AWS CDK CLI: `npm install -g aws-cdk`
- (Recommended) virtual environment

## Installation & Deployment

1. Clone the repository

   ```bash
   git clone https://github.com/aagarwal10-csuchico/url-shortener-aws-cdk.git
   cd url-shortener-aws-cdk
   ```

2. Set up Python virtual environment and install dependencies

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Install & bootstrap CDK (only needed first time)

   ```bash
   npm install -g aws-cdk
   cdk bootstrap
   ```

 4. Deploy the stack

    ```bash
    cdk deploy
    ```

After successful deployment, CDK will output:

- The API Gateway endpoint URL (e.g. https://abc123.execute-api.us-east-1.amazonaws.com/prod/)

## Usage (API)

Assuming your deployed API is at:

```text
https://abc123.execute-api.us-east-1.amazonaws.com/prod
```

1. Shorten a URL

   ```bash
   curl -X POST https://abc123.execute-api.../prod/shorten \
   -H "Content-Type: application/json" \
   -d '{"url": "https://www.example.com/very/long/url"}'
   ```

    Example response:

    ```JSON
    {
      "statusCode": 201
      "short_code": "k9p2m",
      "short_url": "https://abc123.execute-api.../prod/k9p2m",
      "original_url": "https://www.example.com/very/long/url"
    }
    ```

2. Redirect (follow short link)

   ```bash
   curl -L https://abc123.execute-api.us-east-1.amazonaws.com/prod/k9p2m
   ```

## Future Work / Roadmap

- [ ] Frontend – Modern SPA (React / Next.js / Svelte / vanilla JS) with URL shortening form and history
- [ ] Custom domain – Route 53 + ACM certificate + CloudFront (or API Gateway custom domain)
- [ ] Click analytics – Add `click_count` and `last_accessed` to UrlMappings
- [ ] Rate limiting – API Gateway usage plans or Lambda-level throttling
- [ ] OpenAPI / Swagger docs – Auto-generated from CDK
- [ ] CI/CD – GitHub Actions workflow for automated deployment
- [ ] Monitoring – CloudWatch alarms + Lambda insights

## Cleanup

To avoid charges when you're done testing:

```bash
cdk destroy
```

## Known Gotchas & Fixes (from development)

- Access Denied on DynamoDB: Use environment variables for table names (`os.environ["MAPPINGS_TABLE"]`)
- Counter initialization: Added `ensure_counter_exists()` with conditional put
- TypeError on Decimal: Cast `counter_value = int(update_response['Attributes']['value'])`
- Wrong short URL (no stage): Use `event["requestContext"].get("stage")` to build correct prefix
