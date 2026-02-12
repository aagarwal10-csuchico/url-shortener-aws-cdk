
# Serverless URL Shortener

A production-ready, serverless URL shortening service built with **AWS CDK (Python)**, **AWS Lambda**, **Amazon API Gateway**, and **Amazon DynamoDB**.

This project implements a simple yet scalable URL shortener **backend** — perfect for learning serverless architecture, infrastructure as code (IaC), and DynamoDB modeling patterns.

**Currently implemented:**
- Infrastructure as Code with AWS CDK (Python)
- Two DynamoDB tables for URL mappings and atomic counter
- Lambda functions for shortening URLs and handling redirects
- API Gateway REST API with `/urls` (shorten) and `/r/{short_code}` (redirect) endpoints
- Static React frontend (Vite) deployed to S3 and served via CloudFront
- Automatic IAM permissions and resource configuration

**Future work:**
- ~~Modern web frontend~~
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
   curl -X POST https://abc123.execute-api.us-east-1.amazonaws.com/prod/urls \
     -H "Content-Type: application/json" \
     -d '{"long_url": "https://www.example.com/very/long/url"}'
   ```

   Optional request fields:

   - `custom_alias` – custom short code (must be unique)
   - `expiration_date` – ISO-8601 UTC string, e.g. `2026-12-31T23:59:59Z`

   Example success response (HTTP 201 Created):

   ```json
   {
     "short_url": "https://abc123.execute-api.us-east-1.amazonaws.com/prod/r/k9p2m",
     "short_code": "k9p2m",
     "custom_alias": "xyz",
     "expiration_date": "1970-01-01T00:00:00Z"
   }
   ```

   If a `custom_alias` is provided by the user, then `custom_alias` will be present in the response and will take the place of `short_code`. The `expiration_date` field is included in the response only if an expiration was requested.

   On error, the API returns a JSON body like:

   ```json
   { "error": "Invalid URL" }
   ```

2. Redirect (follow short link)

   ```bash
   curl -L https://abc123.execute-api.us-east-1.amazonaws.com/prod/k9p2m
   ```

## Frontend (React SPA)

The project includes a modern React single-page app (built with Vite) that talks to the `/urls` API.

- **Local development:**
  - Set `VITE_API_URL` in `frontend/.env` to your deployed API base URL (e.g. `https://abc123.execute-api.us-east-1.amazonaws.com/prod`)
  - Then:

    ```bash
    cd frontend
    npm install
    npm run dev
    ```

- **Production build:**
  - Build the frontend:

    ```bash
    cd frontend
    npm run build
    ```

  - Deploy via CDK (uploads the contents of `frontend/dist` to S3 and serves via CloudFront):

    ```bash
    cd ..
    cdk deploy
    ```

## Future Work / Roadmap

- [x] Frontend – React SPA with URL shortening form
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
 - CloudFront / browser cache: After deploying frontend changes or updating API/CORS config, you might still see old behavior due to cached assets or preflight responses; create a CloudFront invalidation (e.g. `/*`) and/or hard-refresh / clear browser cache.
