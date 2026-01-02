# 🐦 BirdSense Deployment Guide

**Developed by Soham**  
**Last Updated:** December 31, 2025

This document contains all deployment commands and configurations for BirdSense across multiple cloud platforms.

---

## 🚀 QUICK START - AWS Authentication (Zscaler Compatible)

**Copy-paste these commands when AWS session expires:**

```bash
# Step 1: Fix AWS config (run once if broken)
cat > ~/.aws/config << 'EOF'
[default]
region = ap-south-1
EOF

# Step 2: Set SSL bypass for Zscaler
export AWS_CA_BUNDLE=""
export REQUESTS_CA_BUNDLE=""

# Step 3: Login via browser
aws login

# Step 4: After browser auth, fix config to use login session
cat > ~/.aws/config << 'EOF'
[default]
region = ap-south-1
login_session = arn:aws:sts::205930610456:assumed-role/AWSReservedSSO_DevelopmentAccess_7d2569f648cd3206/soham.niyogi@zycus.com
EOF

# Step 5: Verify it works
aws sts get-caller-identity

# Step 6: Check App Runner services
aws apprunner list-services --region ap-south-1
```

### Current Live Services (December 31, 2025)

| Platform | Service | URL | Status |
|----------|---------|-----|--------|
| **AWS** | Web UI | https://ucpcwpexi5.ap-south-1.awsapprunner.com | ✅ Running |
| **AWS** | API | https://cqxapziyi2.ap-south-1.awsapprunner.com | ✅ Running |
| **GCP** | Web UI | https://birdsense-web-1040356930025.asia-south1.run.app | ✅ Running |
| **GCP** | API | https://birdsense-api-1040356930025.asia-south1.run.app | ✅ Running |

---

## Table of Contents

1. [Quick Start - AWS Authentication](#-quick-start---aws-authentication-zscaler-compatible)
2. [Docker Hub Images](#docker-hub-images)
3. [GCP Cloud Run Deployment](#gcp-cloud-run-deployment)
4. [AWS App Runner Deployment](#aws-app-runner-deployment)
5. [Environment Variables](#environment-variables)
6. [Troubleshooting](#troubleshooting)

---

## Docker Hub Images

| Image | Description | Port |
|-------|-------------|------|
| `sohamzycus/birdsense:latest` | Web UI (Gradio) | 7860 |
| `sohamzycus/birdsense-api:latest` | REST API (FastAPI) | 8000 |

### Build and Push to Docker Hub

```bash
cd /Users/soham.niyogi/Soham/codebase/eagv2/birdsense

# Build for linux/amd64 (required for cloud deployment)
docker buildx build --platform linux/amd64 -t sohamzycus/birdsense:latest --push .
```

---

## GCP Cloud Run Deployment

### Prerequisites
- `gcloud` CLI installed and authenticated
- Docker installed
- `LITELLM_API_KEY` environment variable set

### Deployed URLs (December 31, 2025)

| Service | URL |
|---------|-----|
| 🌐 Web UI | https://birdsense-web-1040356930025.asia-south1.run.app |
| 🔌 REST API | https://birdsense-api-1040356930025.asia-south1.run.app |
| 📚 API Docs | https://birdsense-api-1040356930025.asia-south1.run.app/docs |

### Deploy Web UI to GCP

```bash
export LITELLM_API_KEY='<your-api-key>'

gcloud run deploy birdsense-web \
    --image docker.io/sohamzycus/birdsense:latest \
    --platform managed \
    --region asia-south1 \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 300 \
    --min-instances 0 \
    --max-instances 5 \
    --port 7860 \
    --set-env-vars "RUN_MODE=gradio" \
    --set-env-vars "IS_AZURE=true" \
    --set-env-vars "LITELLM_API_KEY=${LITELLM_API_KEY}" \
    --set-env-vars "LITELLM_API_BASE=https://zycus-ptu.azure-api.net/ptu-intakemanagement" \
    --set-env-vars "AZURE_DEPLOYMENT=gpt4o-130524" \
    --set-env-vars "AZURE_API_VERSION=2024-02-15-preview" \
    --set-env-vars "LITELLM_VISION_MODEL=gpt-4o" \
    --set-env-vars "LITELLM_TEXT_MODEL=gpt-4o" \
    --set-env-vars "GRADIO_SERVER_NAME=0.0.0.0" \
    --set-env-vars "GRADIO_SERVER_PORT=7860"
```

### Deploy REST API to GCP

```bash
export LITELLM_API_KEY='<your-api-key>'
export JWT_SECRET=$(openssl rand -hex 32)

gcloud run deploy birdsense-api \
    --image docker.io/sohamzycus/birdsense:latest \
    --platform managed \
    --region asia-south1 \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 300 \
    --min-instances 0 \
    --max-instances 10 \
    --port 8000 \
    --set-env-vars "RUN_MODE=api" \
    --set-env-vars "IS_AZURE=true" \
    --set-env-vars "LITELLM_API_KEY=${LITELLM_API_KEY}" \
    --set-env-vars "LITELLM_API_BASE=https://zycus-ptu.azure-api.net/ptu-intakemanagement" \
    --set-env-vars "AZURE_DEPLOYMENT=gpt4o-130524" \
    --set-env-vars "AZURE_API_VERSION=2024-02-15-preview" \
    --set-env-vars "LITELLM_VISION_MODEL=gpt-4o" \
    --set-env-vars "LITELLM_TEXT_MODEL=gpt-4o" \
    --set-env-vars "JWT_SECRET_KEY=${JWT_SECRET}"
```

### Quick Deploy Script

```bash
cd /Users/soham.niyogi/Soham/codebase/eagv2/birdsense
export LITELLM_API_KEY='<your-api-key>'
./deploy-gcp.sh
```

---

## AWS App Runner Deployment

### Prerequisites
- AWS CLI v2 installed
- AWS SSO configured
- Docker installed

### AWS Configuration

| Setting | Value |
|---------|-------|
| Account ID | `205930610456` |
| Region | `ap-south-1` (Mumbai) |
| SSO Portal | https://d-9067adaa1d.awsapps.com/start |
| ECR Repository | `ataavi-bird-app/birdsense` |
| IAM Role | `AppRunnerECRAccessRole` |

### Deployed URLs (December 30, 2025)

| Service | URL |
|---------|-----|
| 🌐 Web UI | https://ucpcwpexi5.ap-south-1.awsapprunner.com |
| 🔌 REST API | https://cqxapziyi2.ap-south-1.awsapprunner.com |
| 📚 API Docs | https://cqxapziyi2.ap-south-1.awsapprunner.com/docs |

### Step 1: AWS SSO Login

```bash
# Configure SSO (first time only)
aws configure sso --profile birdsense

# Login via SSO
aws sso login --profile birdsense

# Or use existing default profile if already configured
aws sts get-caller-identity
```

### Step 2: Login to ECR

```bash
export PYTHONHTTPSVERIFY=0
export AWS_CA_BUNDLE=""

aws ecr get-login-password --region ap-south-1 --no-verify-ssl | \
    docker login --username AWS --password-stdin 205930610456.dkr.ecr.ap-south-1.amazonaws.com
```

### Step 3: Create ECR Repository (first time only)

```bash
aws ecr create-repository \
    --repository-name ataavi-bird-app/birdsense \
    --region ap-south-1 \
    --image-scanning-configuration scanOnPush=true \
    --no-verify-ssl
```

### Step 4: Build and Push to ECR

```bash
cd /Users/soham.niyogi/Soham/codebase/eagv2/birdsense

docker buildx build \
    --platform linux/amd64 \
    -t 205930610456.dkr.ecr.ap-south-1.amazonaws.com/ataavi-bird-app/birdsense:latest \
    --push .
```

### Step 5: Create IAM Role for App Runner (first time only)

```bash
# Create trust policy
cat > /tmp/apprunner-trust.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "build.apprunner.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF

# Create role
aws iam create-role \
    --role-name AppRunnerECRAccessRole \
    --assume-role-policy-document file:///tmp/apprunner-trust.json \
    --no-verify-ssl

# Attach ECR policy
aws iam attach-role-policy \
    --role-name AppRunnerECRAccessRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess \
    --no-verify-ssl
```

### Step 6: Deploy Web UI to App Runner

```bash
export LITELLM_API_KEY='<your-api-key>'

aws apprunner create-service \
    --region ap-south-1 \
    --service-name birdsense-web \
    --source-configuration '{
        "ImageRepository": {
            "ImageIdentifier": "205930610456.dkr.ecr.ap-south-1.amazonaws.com/ataavi-bird-app/birdsense:latest",
            "ImageRepositoryType": "ECR",
            "ImageConfiguration": {
                "Port": "7860",
                "RuntimeEnvironmentVariables": {
                    "RUN_MODE": "gradio",
                    "IS_AZURE": "true",
                    "LITELLM_API_KEY": "'"$LITELLM_API_KEY"'",
                    "LITELLM_API_BASE": "https://zycus-ptu.azure-api.net/ptu-intakemanagement",
                    "AZURE_DEPLOYMENT": "gpt4o-130524",
                    "AZURE_API_VERSION": "2024-02-15-preview",
                    "LITELLM_VISION_MODEL": "gpt-4o",
                    "LITELLM_TEXT_MODEL": "gpt-4o"
                }
            }
        },
        "AutoDeploymentsEnabled": true,
        "AuthenticationConfiguration": {
            "AccessRoleArn": "arn:aws:iam::205930610456:role/service-role/AppRunnerECRAccessRole"
        }
    }' \
    --instance-configuration '{"Cpu": "2 vCPU", "Memory": "4 GB"}' \
    --no-verify-ssl
```

### Step 7: Deploy REST API to App Runner

```bash
export LITELLM_API_KEY='<your-api-key>'
export JWT_SECRET=$(openssl rand -hex 32)

aws apprunner create-service \
    --region ap-south-1 \
    --service-name birdsense-api \
    --source-configuration '{
        "ImageRepository": {
            "ImageIdentifier": "205930610456.dkr.ecr.ap-south-1.amazonaws.com/ataavi-bird-app/birdsense:latest",
            "ImageRepositoryType": "ECR",
            "ImageConfiguration": {
                "Port": "8000",
                "RuntimeEnvironmentVariables": {
                    "RUN_MODE": "api",
                    "IS_AZURE": "true",
                    "LITELLM_API_KEY": "'"$LITELLM_API_KEY"'",
                    "LITELLM_API_BASE": "https://zycus-ptu.azure-api.net/ptu-intakemanagement",
                    "AZURE_DEPLOYMENT": "gpt4o-130524",
                    "AZURE_API_VERSION": "2024-02-15-preview",
                    "LITELLM_VISION_MODEL": "gpt-4o",
                    "LITELLM_TEXT_MODEL": "gpt-4o",
                    "JWT_SECRET_KEY": "'"$JWT_SECRET"'"
                }
            }
        },
        "AutoDeploymentsEnabled": true,
        "AuthenticationConfiguration": {
            "AccessRoleArn": "arn:aws:iam::205930610456:role/service-role/AppRunnerECRAccessRole"
        }
    }' \
    --instance-configuration '{"Cpu": "2 vCPU", "Memory": "4 GB"}' \
    --no-verify-ssl
```

### Update Existing Services

```bash
# Get service ARN
aws apprunner list-services --region ap-south-1 --no-verify-ssl

# Trigger new deployment (after pushing new image to ECR)
aws apprunner start-deployment \
    --service-arn "arn:aws:apprunner:ap-south-1:205930610456:service/birdsense-web/SERVICE_ID" \
    --region ap-south-1 \
    --no-verify-ssl
```

### Delete Services

```bash
# Delete Web UI
aws apprunner delete-service \
    --service-arn "arn:aws:apprunner:ap-south-1:205930610456:service/birdsense-web/SERVICE_ID" \
    --region ap-south-1 \
    --no-verify-ssl

# Delete API
aws apprunner delete-service \
    --service-arn "arn:aws:apprunner:ap-south-1:205930610456:service/birdsense-api/SERVICE_ID" \
    --region ap-south-1 \
    --no-verify-ssl
```

---

## Environment Variables

### Required for All Deployments

| Variable | Value | Description |
|----------|-------|-------------|
| `LITELLM_API_KEY` | `<your-api-key>` | Azure OpenAI API Key (get from team) |
| `LITELLM_API_BASE` | `https://zycus-ptu.azure-api.net/ptu-intakemanagement` | Azure endpoint |
| `AZURE_DEPLOYMENT` | `gpt4o-130524` | Model deployment name |
| `AZURE_API_VERSION` | `2024-02-15-preview` | API version |
| `IS_AZURE` | `true` | Use Azure OpenAI |
| `LITELLM_VISION_MODEL` | `gpt-4o` | Vision model |
| `LITELLM_TEXT_MODEL` | `gpt-4o` | Text model |

### Web UI Specific

| Variable | Value |
|----------|-------|
| `RUN_MODE` | `gradio` |
| `GRADIO_SERVER_NAME` | `0.0.0.0` |
| `GRADIO_SERVER_PORT` | `7860` |

### API Specific

| Variable | Value |
|----------|-------|
| `RUN_MODE` | `api` |
| `JWT_SECRET_KEY` | `<generated with openssl rand -hex 32>` |

---

## Troubleshooting

### AWS SSL Certificate Issues

If you encounter SSL certificate errors:

```bash
# Option 1: Disable SSL verification
export PYTHONHTTPSVERIFY=0
export AWS_CA_BUNDLE=""
aws <command> --no-verify-ssl

# Option 2: Fix certificates on macOS
/Applications/Python\ 3.12/Install\ Certificates.command

# Option 3: Update certifi
pip install --upgrade certifi
export SSL_CERT_FILE=$(python3 -c "import certifi; print(certifi.where())")
```

### Check Service Status

```bash
# GCP
gcloud run services list --region asia-south1

# AWS
aws apprunner list-services --region ap-south-1 --no-verify-ssl
```

### View Logs

```bash
# GCP
gcloud run services logs read birdsense-web --region asia-south1

# AWS
aws logs describe-log-groups --log-group-name-prefix /aws/apprunner --no-verify-ssl
```

### Local Testing

```bash
cd /Users/soham.niyogi/Soham/codebase/eagv2/birdsense
source venv/bin/activate

# Run Web UI
python app.py --port 7860

# Run API
RUN_MODE=api uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## Summary of Deployed Services

### GCP Cloud Run (asia-south1)

| Service | URL | Specs |
|---------|-----|-------|
| birdsense-web | https://birdsense-web-1040356930025.asia-south1.run.app | 2 CPU, 4GB RAM |
| birdsense-api | https://birdsense-api-1040356930025.asia-south1.run.app | 2 CPU, 4GB RAM |

### AWS App Runner (ap-south-1)

| Service | URL | Specs |
|---------|-----|-------|
| birdsense-web | https://ucpcwpexi5.ap-south-1.awsapprunner.com | 2 vCPU, 4GB RAM |
| birdsense-api | https://cqxapziyi2.ap-south-1.awsapprunner.com | 2 vCPU, 4GB RAM |

---

## Quick Reference Commands

```bash
# === GCP Deployment ===
cd /Users/soham.niyogi/Soham/codebase/eagv2/birdsense
export LITELLM_API_KEY='<your-api-key>'
./deploy-gcp.sh

# === AWS Deployment ===
cd /Users/soham.niyogi/Soham/codebase/eagv2/birdsense
export PYTHONHTTPSVERIFY=0 && export AWS_CA_BUNDLE=""
./deploy-aws.sh

# === Local Development ===
cd /Users/soham.niyogi/Soham/codebase/eagv2/birdsense
source venv/bin/activate
python app.py --port 7860
```

---

---

## 🔄 Quick Redeploy Commands

### Redeploy to AWS (after code changes)

```bash
# Set environment
export AWS_CA_BUNDLE=""
export LITELLM_API_KEY='<your-api-key>'

# Build and push new image
cd /Users/soham.niyogi/Soham/codebase/eagv2/birdsense
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 205930610456.dkr.ecr.ap-south-1.amazonaws.com
docker buildx build --platform linux/amd64 -t 205930610456.dkr.ecr.ap-south-1.amazonaws.com/ataavi-bird-app/birdsense:latest --push .

# Trigger redeployment
aws apprunner start-deployment --service-arn "arn:aws:apprunner:ap-south-1:205930610456:service/birdsense-web/243cde5150e446859f1991bf25d47cb0" --region ap-south-1
aws apprunner start-deployment --service-arn "arn:aws:apprunner:ap-south-1:205930610456:service/birdsense-api/f368a2873ea6468cbdb7ca4602827bca" --region ap-south-1
```

### Redeploy to GCP (after code changes)

```bash
export LITELLM_API_KEY='<your-api-key>'

# Build and push to Docker Hub
cd /Users/soham.niyogi/Soham/codebase/eagv2/birdsense
docker buildx build --platform linux/amd64 -t sohamzycus/birdsense:latest --push .

# Redeploy (Cloud Run auto-pulls latest)
gcloud run services update birdsense-web --image docker.io/sohamzycus/birdsense:latest --region asia-south1
gcloud run services update birdsense-api --image docker.io/sohamzycus/birdsense:latest --region asia-south1
```

---

*Document created: December 30, 2025*  
*Last updated: December 31, 2025*

