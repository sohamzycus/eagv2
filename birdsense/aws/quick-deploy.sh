#!/bin/bash
# 🐦 BirdSense Quick Deploy to AWS
# One-command deployment using CloudFormation
#
# Usage: ./quick-deploy.sh YOUR_API_KEY
#
# This script:
# 1. Builds Docker image
# 2. Creates ECR repository  
# 3. Pushes image to ECR
# 4. Deploys CloudFormation stack (full infrastructure)
# 5. Outputs the URL

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

AWS_REGION="ap-south-1"
STACK_NAME="birdsense"

# Get API key from argument or environment
API_KEY="${1:-$LITELLM_API_KEY}"

if [ -z "$API_KEY" ]; then
    echo -e "${RED}Error: API key required${NC}"
    echo "Usage: ./quick-deploy.sh YOUR_API_KEY"
    echo "   Or: export LITELLM_API_KEY=xxx && ./quick-deploy.sh"
    exit 1
fi

echo ""
echo -e "${BLUE}🐦 BirdSense Quick Deploy to AWS${NC}"
echo "=================================="
echo ""

# Check prerequisites
echo -e "${BLUE}[1/6]${NC} Checking prerequisites..."
command -v aws >/dev/null 2>&1 || { echo -e "${RED}AWS CLI not found${NC}"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker not found${NC}"; exit 1; }
aws sts get-caller-identity >/dev/null 2>&1 || { echo -e "${RED}AWS not configured${NC}"; exit 1; }

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/birdsense"

echo -e "${GREEN}✓${NC} AWS Account: ${AWS_ACCOUNT_ID}"
echo -e "${GREEN}✓${NC} Region: ${AWS_REGION}"

# Create ECR repository (if not exists)
echo ""
echo -e "${BLUE}[2/6]${NC} Creating ECR repository..."
aws ecr create-repository \
    --repository-name birdsense \
    --region ${AWS_REGION} \
    --image-scanning-configuration scanOnPush=true \
    2>/dev/null && echo -e "${GREEN}✓${NC} ECR repository created" \
    || echo -e "${YELLOW}⚠${NC} ECR repository already exists"

# Build Docker image
echo ""
echo -e "${BLUE}[3/6]${NC} Building Docker image..."
cd "$(dirname "$0")/.."
docker build -t birdsense:latest . --quiet
echo -e "${GREEN}✓${NC} Image built"

# Push to ECR
echo ""
echo -e "${BLUE}[4/6]${NC} Pushing image to ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com >/dev/null
docker tag birdsense:latest ${ECR_URI}:latest
docker push ${ECR_URI}:latest --quiet
echo -e "${GREEN}✓${NC} Image pushed to ECR"

# Deploy CloudFormation
echo ""
echo -e "${BLUE}[5/6]${NC} Deploying infrastructure (this takes ~5 minutes)..."

# Check if stack exists
STACK_EXISTS=$(aws cloudformation describe-stacks --stack-name ${STACK_NAME} --region ${AWS_REGION} 2>/dev/null || echo "")

if [ -z "$STACK_EXISTS" ]; then
    # Create new stack
    aws cloudformation create-stack \
        --stack-name ${STACK_NAME} \
        --template-body file://aws/cloudformation.yaml \
        --parameters \
            ParameterKey=LiteLLMApiKey,ParameterValue="${API_KEY}" \
            ParameterKey=RunMode,ParameterValue=both \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --region ${AWS_REGION} \
        --output text >/dev/null
    
    echo "  Creating stack..."
    aws cloudformation wait stack-create-complete --stack-name ${STACK_NAME} --region ${AWS_REGION}
else
    # Update existing stack
    aws cloudformation update-stack \
        --stack-name ${STACK_NAME} \
        --template-body file://aws/cloudformation.yaml \
        --parameters \
            ParameterKey=LiteLLMApiKey,ParameterValue="${API_KEY}" \
            ParameterKey=RunMode,ParameterValue=both \
        --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
        --region ${AWS_REGION} \
        --output text >/dev/null 2>&1 || true
    
    echo "  Updating stack..."
    aws cloudformation wait stack-update-complete --stack-name ${STACK_NAME} --region ${AWS_REGION} 2>/dev/null || true
fi

echo -e "${GREEN}✓${NC} Infrastructure deployed"

# Get outputs
echo ""
echo -e "${BLUE}[6/6]${NC} Getting deployment URLs..."

ALB_URL=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query "Stacks[0].Outputs[?OutputKey=='ALBURL'].OutputValue" \
    --output text \
    --region ${AWS_REGION})

echo ""
echo "========================================"
echo -e "${GREEN}🎉 BirdSense Deployed Successfully!${NC}"
echo "========================================"
echo ""
echo -e "🌐 ${GREEN}Web UI:${NC}    ${ALB_URL}"
echo -e "🔌 ${GREEN}REST API:${NC}  ${ALB_URL}/api"
echo -e "📚 ${GREEN}API Docs:${NC}  ${ALB_URL}/docs"
echo ""
echo "Note: It may take 1-2 minutes for the service to become fully available."
echo ""
echo -e "${YELLOW}To update the application:${NC}"
echo "  docker build -t birdsense . && docker push ${ECR_URI}:latest"
echo "  aws ecs update-service --cluster birdsense-cluster --service birdsense-service --force-new-deployment --region ${AWS_REGION}"
echo ""
echo -e "${YELLOW}To delete:${NC}"
echo "  aws cloudformation delete-stack --stack-name ${STACK_NAME} --region ${AWS_REGION}"
echo ""

