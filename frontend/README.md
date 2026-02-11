# URL Shortener Frontend

React + Vite + Tailwind frontend for the URL shortener.

## Setup

```bash
npm install
cp .env.example .env
# Edit .env with your VITE_API_URL and VITE_GITHUB_REPO
```

## Development

```bash
npm run dev
```

## Build (required before `cdk deploy`)

```bash
npm run build
```

This creates `frontend/dist`. The CDK stack deploys from this folder to S3/CloudFront.
