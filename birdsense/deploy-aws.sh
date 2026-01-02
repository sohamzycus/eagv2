#!/bin/bash
# 🐦 BirdSense - AWS Deployment (Web UI + API)
# Developed by Soham
#
# Deploys to AWS App Runner using ECR
# ECR Repository: ataavi-bird-app/birdsense
#
# Prerequisites:
# 1. AWS CLI v2 installed
# 2. Docker installed and running
# 3. AWS credentials configured (SSO or IAM)
#
# Usage:
#   ./deploy-aws.sh              # Deploy both web and API
#   ./deploy-aws.sh web          # Deploy web UI only
#   ./deploy-aws.sh api          # Deploy API only
#   ./deploy-aws.sh push         # Just build and push to ECR

set -e

# ============ SSL FIX FOR AWS CLI ============
export PYTHONHTTPSVERIFY=0
export AWS_CA_BUNDLE=""

# ============ CONFIGURATION ============
AWS_REGION="ap-south-1"
AWS_ACCOUNT_ID="205930610456"
ECR_REPO="ataavi-bird-app/birdsense"
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"

# App Runner Configuration
WEB_SERVICE="birdsense-web"
API_SERVICE="birdsense-api"
IAM_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/service-role/AppRunnerECRAccessRole"

# API Key - MUST be set as environment variable
LITELLM_API_KEY="${LITELLM_API_KEY:-}"

if [ -z "$LITELLM_API_KEY" ]; then
    echo -e "${RED}❌ LITELLM_API_KEY not set.${NC}"
    echo "Export it first: export LITELLM_API_KEY='your-api-key'"
    exit 1
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}🐦 BirdSense - AWS Deployment${NC}"
echo "================================"
echo -e "Account: ${GREEN}${AWS_ACCOUNT_ID}${NC}"
echo -e "Region:  ${GREEN}${AWS_REGION}${NC}"
echo -e "ECR:     ${GREEN}${ECR_REPO}${NC}"
echo ""

# ============ CHECK PREREQUISITES ============
check_prerequisites() {
    echo -e "${BLUE}[1/5]${NC} Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found.${NC}"
        exit 1
    fi
    
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI not found.${NC}"
        exit 1
    fi
    
    # Verify AWS credentials
    if ! aws sts get-caller-identity --no-verify-ssl &>/dev/null 2>&1; then
        echo -e "${RED}❌ AWS credentials not valid. Please login first.${NC}"
        echo "Run: aws sso login"
        exit 1
    fi
    
    echo -e "${GREEN}✓${NC} Prerequisites OK"
}

# ============ LOGIN TO ECR ============
ecr_login() {
    echo ""
    echo -e "${BLUE}[2/5]${NC} Logging into ECR..."
    
    aws ecr get-login-password --region ${AWS_REGION} --no-verify-ssl 2>/dev/null | \
        docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
    
    echo -e "${GREEN}✓${NC} ECR login successful"
}

# ============ BUILD AND PUSH ============
build_and_push() {
    echo ""
    echo -e "${BLUE}[3/5]${NC} Building and pushing Docker image..."
    
    cd "$(dirname "$0")"
    
    docker buildx build \
        --platform linux/amd64 \
        -t ${ECR_URI}:latest \
        -t ${ECR_URI}:$(date +%Y%m%d-%H%M%S) \
        --push \
        .
    
    echo -e "${GREEN}✓${NC} Image pushed to ${ECR_URI}:latest"
}

# ============ DEPLOY WEB UI ============
deploy_web() {
    echo ""
    echo -e "${BLUE}[4/5]${NC} Deploying Web UI to App Runner..."
    
    # Check if service exists
    SERVICE_ARN=$(aws apprunner list-services --region ${AWS_REGION} --no-verify-ssl 2>/dev/null \
        | grep -o '"ServiceArn": "[^"]*birdsense-web[^"]*"' | cut -d'"' -f4 || echo "")
    
    if [ -z "$SERVICE_ARN" ]; then
        echo "  Creating new App Runner service..."
        
        aws apprunner create-service \
            --region ${AWS_REGION} \
            --service-name ${WEB_SERVICE} \
            --source-configuration '{
                "ImageRepository": {
                    "ImageIdentifier": "'"${ECR_URI}"':latest",
                    "ImageRepositoryType": "ECR",
                    "ImageConfiguration": {
                        "Port": "7860",
                        "RuntimeEnvironmentVariables": {
                            "RUN_MODE": "gradio",
                            "IS_AZURE": "true",
                            "LITELLM_API_KEY": "'"${LITELLM_API_KEY}"'",
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
                    "AccessRoleArn": "'"${IAM_ROLE_ARN}"'"
                }
            }' \
            --instance-configuration '{"Cpu": "2 vCPU", "Memory": "4 GB"}' \
            --no-verify-ssl 2>&1 | grep -v "InsecureRequestWarning\|warnings.warn"
    else
        echo "  Updating existing service..."
        aws apprunner start-deployment \
            --service-arn ${SERVICE_ARN} \
            --region ${AWS_REGION} \
            --no-verify-ssl 2>&1 | grep -v "InsecureRequestWarning\|warnings.warn"
    fi
    
    echo -e "${GREEN}✓${NC} Web UI deployment initiated"
}

# ============ DEPLOY API ============
deploy_api() {
    echo ""
    echo -e "${BLUE}[5/5]${NC} Deploying REST API to App Runner..."
    
    JWT_SECRET=$(openssl rand -hex 32)
    
    # Check if service exists
    SERVICE_ARN=$(aws apprunner list-services --region ${AWS_REGION} --no-verify-ssl 2>/dev/null \
        | grep -o '"ServiceArn": "[^"]*birdsense-api[^"]*"' | cut -d'"' -f4 || echo "")
    
    if [ -z "$SERVICE_ARN" ]; then
        echo "  Creating new App Runner service..."
        
        aws apprunner create-service \
            --region ${AWS_REGION} \
            --service-name ${API_SERVICE} \
            --source-configuration '{
                "ImageRepository": {
                    "ImageIdentifier": "'"${ECR_URI}"':latest",
                    "ImageRepositoryType": "ECR",
                    "ImageConfiguration": {
                        "Port": "8000",
                        "RuntimeEnvironmentVariables": {
                            "RUN_MODE": "api",
                            "IS_AZURE": "true",
                            "LITELLM_API_KEY": "'"${LITELLM_API_KEY}"'",
                            "LITELLM_API_BASE": "https://zycus-ptu.azure-api.net/ptu-intakemanagement",
                            "AZURE_DEPLOYMENT": "gpt4o-130524",
                            "AZURE_API_VERSION": "2024-02-15-preview",
                            "LITELLM_VISION_MODEL": "gpt-4o",
                            "LITELLM_TEXT_MODEL": "gpt-4o",
                            "JWT_SECRET_KEY": "'"${JWT_SECRET}"'"
                        }
                    }
                },
                "AutoDeploymentsEnabled": true,
                "AuthenticationConfiguration": {
                    "AccessRoleArn": "'"${IAM_ROLE_ARN}"'"
                }
            }' \
            --instance-configuration '{"Cpu": "2 vCPU", "Memory": "4 GB"}' \
            --no-verify-ssl 2>&1 | grep -v "InsecureRequestWarning\|warnings.warn"
    else
        echo "  Updating existing service..."
        aws apprunner start-deployment \
            --service-arn ${SERVICE_ARN} \
            --region ${AWS_REGION} \
            --no-verify-ssl 2>&1 | grep -v "InsecureRequestWarning\|warnings.warn"
    fi
    
    echo -e "${GREEN}✓${NC} API deployment initiated"
}

# ============ PRINT SUMMARY ============
print_summary() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}🎉 BirdSense AWS Deployment Complete!${NC}"
    echo "=========================================="
    echo ""
    echo "ECR Image: ${ECR_URI}:latest"
    echo ""
    echo "Services (check status in ~5 minutes):"
    echo "  Web UI:   https://<id>.${AWS_REGION}.awsapprunner.com"
    echo "  REST API: https://<id>.${AWS_REGION}.awsapprunner.com"
    echo ""
    echo "Check status:"
    echo "  aws apprunner list-services --region ${AWS_REGION} --no-verify-ssl"
    echo ""
}

# ============ MAIN ============
MODE=${1:-both}

check_prerequisites

case $MODE in
    push)
        ecr_login
        build_and_push
        ;;
    web)
        ecr_login
        build_and_push
        deploy_web
        print_summary
        ;;
    api)
        ecr_login
        build_and_push
        deploy_api
        print_summary
        ;;
    both|*)
        ecr_login
        build_and_push
        deploy_web
        deploy_api
        print_summary
        ;;
esac
