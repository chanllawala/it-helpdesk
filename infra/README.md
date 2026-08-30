# AWS deployment

Terraform for running the helpdesk on AWS: React build on S3 behind
CloudFront, FastAPI container on ECS, data in RDS PostgreSQL, deployed by
GitHub Actions.

## Architecture

```
                        ┌──────────────┐
     browser ──HTTPS──▶ │  CloudFront  │
                        └──────┬───────┘
                    /*         │        /api/*
              ┌────────────────┴────────────────┐
              ▼                                 ▼
       ┌─────────────┐                 ┌──────────────────┐
       │  S3 bucket  │                 │  EC2 (ECS agent) │
       │ React build │                 │  backend task    │
       │  (private)  │                 │  :8000           │
       └─────────────┘                 └────────┬─────────┘
         via OAC                                │
                                                ▼
                                        ┌──────────────┐
                                        │ RDS Postgres │
                                        │  (private)   │
                                        └──────────────┘
```

**One distribution serves both halves.** The frontend is at `/`, the API at
`/api/*`. That is deliberate, and it is the design decision the rest of the
architecture hangs off — see "the problem worth reading about" below.

## Why ECS on EC2 rather than Fargate

Fargate has no free tier. A single 0.25 vCPU task runs about $9/month, and the
load balancer you would normally put in front of it is another $18. ECS on a
`t3.micro` container instance costs nothing for the first twelve months and
exercises the same ECR push, task definition and rolling-deploy mechanics.

The trade-off is honest: one instance publishing a fixed host port cannot run
two copies of the task at once, so each deploy stops the old container before
starting the new one — a few seconds of downtime. A second instance, or a load
balancer, removes it.

## The problem worth reading about

The first working shape of this was the obvious one: S3 and CloudFront serving
the frontend over HTTPS, and the browser calling the API directly on the
container instance's public address.

It does not work, for two compounding reasons.

**Mixed content.** CloudFront serves the page over HTTPS. The API had no TLS,
because a certificate cannot be issued for an AWS-assigned hostname like
`ec2-3-8-1-2.eu-west-2.compute.amazonaws.com` — you have to own the domain.
Browsers block an HTTPS page from calling an HTTP endpoint outright, and the
failure surfaces as a generic network error in the console rather than
anything that names the real cause.

**CORS.** Even over HTTPS, the frontend and API were different origins, so
every request needed a preflight and a correctly configured allow-list — and
the allowed origin is the CloudFront domain, which does not exist until after
the distribution is created.

Both dissolve if the two are the same origin. Adding a second CloudFront
origin pointing at the container instance, with an `/api/*` cache behaviour in
front of it, means:

- the browser only ever talks to CloudFront over HTTPS, so no mixed content
- requests are same-origin, so CORS does not apply at all and
  `CORS_ORIGINS` is empty in the task definition
- CloudFront reaches the origin over plain HTTP inside AWS, which is fine
  because the instance's security group admits nothing else

That last point needed the API to be mounted under `/api`, which is why
`API_PREFIX` exists in the backend config. It defaults to empty so the Render
deployment, where the API has its own hostname, is unaffected.

Two smaller things fell out of the same change:

- **The API cache behaviour must disable caching** and forward the
  `Authorization` header. CloudFront's default policy strips it, and the
  symptom is every authenticated request returning 401 with no clue why.
- **`index.html` must not be cached like the other assets.** The hashed JS and
  CSS are immutable and cached for a year; `index.html` is `no-cache`, or
  browsers keep loading the previous build's asset references after a deploy.

## Other decisions

**Default VPC.** A purpose-built VPC with private subnets needs a NAT gateway
for the container instance to pull images — about $32/month, more than
everything else here combined.

**A fixed Elastic IP.** The instance sits in an autoscaling group of one, so a
replacement would come back on a new address and silently break CloudFront's
origin. The instance claims a pre-allocated Elastic IP on boot instead, which
is free while attached. A load balancer is the usual answer and costs $18.

**Secrets are generated, never typed.** Terraform generates the database
password and JWT signing key, stores them in Secrets Manager, and ECS injects
them at container start. They are never in the repository and nobody handles
the values. They do land in Terraform state, which is why state should move to
an encrypted S3 backend before more than one person touches this.

**Keyless CI.** GitHub Actions assumes an IAM role via OIDC rather than
storing access keys as repository secrets. The trust policy is scoped to this
repository — without that condition, any repository on GitHub could assume the
role.

**No inbound SSH.** There is no port 22 rule. Shell access is through Session
Manager, which needs no open port and no key to lose.

## Deploying

Requires the AWS CLI configured with credentials for an IAM user (not root)
and Terraform ≥ 1.6.

```bash
cd infra
terraform init
terraform apply
```

Then publish the first image, since ECS has nothing to run until one exists:

```bash
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGION=$(terraform output -raw region 2>/dev/null || echo eu-west-2)
REPO=$(terraform output -raw ecr_repository_url)

aws ecr get-login-password --region "$REGION" \
  | docker login --username AWS --password-stdin "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"

cd ../backend
docker build -t "$REPO:latest" .
docker push "$REPO:latest"
```

And the frontend:

```bash
cd ../frontend
VITE_API_URL=/api npm run build
aws s3 sync dist/ "s3://$(cd ../infra && terraform output -raw frontend_bucket)/" --delete
```

`terraform output site_url` is the application.

## Wiring up automatic deploys

`terraform output github_actions_values` prints the repository **variables**
to set under Settings → Secrets and variables → Actions, plus
`terraform output github_actions_role_arn` for `AWS_ROLE_ARN`.

There are no secrets to add — OIDC replaces them. The deploy job checks for
`AWS_ROLE_ARN` and skips itself when it is absent, so CI stays green before
any of this exists.

## Costs

Free for the first twelve months, assuming one instance and one database:

| | |
| --- | --- |
| EC2 `t3.micro` | 750 h/month free tier |
| RDS `db.t3.micro` | 750 h/month free tier, 20 GB |
| ECR | 500 MB free; a lifecycle policy keeps only the last 10 images |
| S3 + CloudFront | negligible at this traffic |
| Elastic IP | free while attached; 750 h/month free tier |
| Secrets Manager | ~$0.40/month per secret — the one line item that is not free |

After twelve months the EC2 and RDS instances become chargeable, roughly
$8 and $15 a month. `terraform destroy` removes everything.
