# 🐦 BirdSense AWS Deployment

Deploy BirdSense to **AWS ap-south-1 (Mumbai)** using ECS Fargate or App Runner.

## 📋 Prerequisites

1. **AWS CLI** configured with credentials
   ```bash
   aws configure
   # Enter your Access Key, Secret Key, Region: ap-south-1
   ```

2. **Docker** installed and running

3. **LiteLLM API Key** (Azure OpenAI)
   ```bash
   export LITELLM_API_KEY="your-api-key-here"
   ```

## 🚀 Quick Deploy (Recommended)

### Option 1: Shell Script (ECS Fargate)

```bash
# First-time setup (creates ECR, ECS cluster, etc.)
cd aws
chmod +x deploy.sh
./deploy.sh --setup

# Deploy Web UI
./deploy.sh --mode gradio

# Or deploy REST API only
./deploy.sh --mode api

# Or deploy both
./deploy.sh --mode both
```

### Option 2: CloudFormation (One-Click)

```bash
aws cloudformation create-stack \
  --stack-name birdsense \
  --template-body file://aws/cloudformation.yaml \
  --parameters ParameterKey=LiteLLMApiKey,ParameterValue=$LITELLM_API_KEY \
  --capabilities CAPABILITY_IAM \
  --region ap-south-1
```

Wait ~5 minutes, then get the URL:
```bash
aws cloudformation describe-stacks \
  --stack-name birdsense \
  --query "Stacks[0].Outputs" \
  --output table \
  --region ap-south-1
```

## 📁 Files

| File | Description |
|------|-------------|
| `deploy.sh` | Interactive deployment script |
| `cloudformation.yaml` | Full infrastructure as code |
| `apprunner.yaml` | App Runner config (simpler) |

## 🏗️ Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │            AWS ap-south-1 (Mumbai)          │
                    │                                             │
    Users ──────────┤  ┌───────────────────────────────────────┐  │
                    │  │     Application Load Balancer         │  │
                    │  │   (birdsense-alb.ap-south-1.elb.aws)  │  │
                    │  └───────────────┬───────────────────────┘  │
                    │                  │                          │
                    │         ┌────────┴────────┐                 │
                    │         │                 │                 │
                    │  ┌──────▼──────┐  ┌───────▼──────┐         │
                    │  │  Port 7860  │  │  Port 8000   │         │
                    │  │   Web UI    │  │   REST API   │         │
                    │  │  (Gradio)   │  │  (FastAPI)   │         │
                    │  └──────┬──────┘  └───────┬──────┘         │
                    │         │                 │                 │
                    │  ┌──────┴─────────────────┴──────┐         │
                    │  │        ECS Fargate Task        │         │
                    │  │   ┌─────────────────────────┐  │         │
                    │  │   │   BirdSense Container   │  │         │
                    │  │   │                         │  │         │
                    │  │   │  • BirdNET (Cornell)    │  │         │
                    │  │   │  • Azure OpenAI/GPT-4o  │  │         │
                    │  │   │  • SAM-Audio           │  │         │
                    │  │   └─────────────────────────┘  │         │
                    │  └────────────────────────────────┘         │
                    │                                             │
                    │  ┌────────────┐  ┌─────────────────────┐   │
                    │  │    ECR     │  │  SSM Parameter Store │   │
                    │  │ (birdsense)│  │   (API Key stored)   │   │
                    │  └────────────┘  └─────────────────────┘   │
                    └─────────────────────────────────────────────┘
```

## 💰 Estimated Costs

| Resource | Spec | Cost/Month |
|----------|------|------------|
| ECS Fargate | 1 vCPU, 2GB RAM | ~$30 |
| ALB | Per hour + LCU | ~$20 |
| ECR | Image storage | ~$1 |
| CloudWatch | Logs | ~$5 |
| **Total** | | **~$56/month** |

### Cost Optimization Tips

1. **Use Fargate Spot** for dev/test (70% cheaper):
   ```yaml
   CapacityProvider: FARGATE_SPOT
   ```

2. **Scale to zero** when not in use:
   ```bash
   aws ecs update-service --cluster birdsense-cluster --service birdsense-service --desired-count 0
   ```

3. **Use App Runner** for simpler billing (pay per request)

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LITELLM_API_KEY` | ✅ | Azure OpenAI API key |
| `RUN_MODE` | ❌ | `gradio`, `api`, or `both` |
| `IS_AZURE` | ❌ | Set to `true` for Azure |
| `LITELLM_API_BASE` | ❌ | Azure endpoint URL |

### Updating the API Key

```bash
aws ssm put-parameter \
  --name "/birdsense/litellm-api-key" \
  --type "SecureString" \
  --value "NEW_API_KEY" \
  --overwrite \
  --region ap-south-1

# Force new deployment to pick up changes
aws ecs update-service \
  --cluster birdsense-cluster \
  --service birdsense-service \
  --force-new-deployment \
  --region ap-south-1
```

## 📊 Monitoring

### View Logs

```bash
aws logs tail /ecs/birdsense --follow --region ap-south-1
```

### Check Service Status

```bash
aws ecs describe-services \
  --cluster birdsense-cluster \
  --services birdsense-service \
  --region ap-south-1
```

### CloudWatch Dashboard

Visit: https://ap-south-1.console.aws.amazon.com/cloudwatch/home?region=ap-south-1#dashboards:

## 🔄 Updating the Application

```bash
# Build and push new image
cd /path/to/birdsense
docker build -t birdsense .
docker tag birdsense:latest ${ACCOUNT_ID}.dkr.ecr.ap-south-1.amazonaws.com/birdsense:latest
docker push ${ACCOUNT_ID}.dkr.ecr.ap-south-1.amazonaws.com/birdsense:latest

# Force new deployment
aws ecs update-service \
  --cluster birdsense-cluster \
  --service birdsense-service \
  --force-new-deployment \
  --region ap-south-1
```

## 🗑️ Cleanup

### Delete CloudFormation Stack
```bash
aws cloudformation delete-stack --stack-name birdsense --region ap-south-1
```

### Manual Cleanup
```bash
# Stop service
aws ecs update-service --cluster birdsense-cluster --service birdsense-service --desired-count 0 --region ap-south-1

# Delete service
aws ecs delete-service --cluster birdsense-cluster --service birdsense-service --force --region ap-south-1

# Delete cluster
aws ecs delete-cluster --cluster birdsense-cluster --region ap-south-1

# Delete ECR repository
aws ecr delete-repository --repository-name birdsense --force --region ap-south-1
```

## 🆘 Troubleshooting

### Container won't start
```bash
# Check task logs
aws ecs describe-tasks --cluster birdsense-cluster --tasks <TASK_ARN> --region ap-south-1
```

### Health check failing
- Make sure port 7860 (UI) or 8000 (API) is accessible
- Check container logs for errors

### API key issues
```bash
# Verify SSM parameter exists
aws ssm get-parameter --name "/birdsense/litellm-api-key" --with-decryption --region ap-south-1
```

---

**🐦 BirdSense by Soham** | AWS Deployment Guide

