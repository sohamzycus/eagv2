#!/bin/bash
# 🐦 BirdSense AWS Deployment Script
# Developed by Soham
# 
# Deploys to AWS ap-south-1 (Mumbai) using:
# - ECR for container registry
# - ECS Fargate for serverless container hosting
#
# Prerequisites:
# 1. AWS CLI configured with credentials
# 2. Docker installed and running
# 3. LITELLM_API_KEY set in environment or .env file
#
# Usage:
#   ./deploy.sh                    # Deploy Gradio UI (default)
#   ./deploy.sh --mode api         # Deploy REST API only
#   ./deploy.sh --mode both        # Deploy both UI and API
#   ./deploy.sh --setup            # First-time setup (creates ECR, ECS cluster, etc.)

set -e

# ============ CONFIGURATION ============
AWS_REGION="ap-south-1"
ECR_REPO_NAME="birdsense"
ECS_CLUSTER_NAME="birdsense-cluster"
ECS_SERVICE_NAME="birdsense-service"
TASK_FAMILY="birdsense-task"
CONTAINER_PORT_UI=7860
CONTAINER_PORT_API=8000
CPU="1024"         # 1 vCPU
MEMORY="2048"      # 2 GB RAM
RUN_MODE="gradio"  # gradio, api, or both

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============ PARSE ARGUMENTS ============
SETUP_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            RUN_MODE="$2"
            shift 2
            ;;
        --setup)
            SETUP_MODE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--mode gradio|api|both] [--setup]"
            echo ""
            echo "Options:"
            echo "  --mode    Deployment mode (gradio, api, or both)"
            echo "  --setup   First-time setup (creates ECR, ECS cluster, etc.)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# ============ HELPERS ============
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ============ CHECK PREREQUISITES ============
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Install: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Install: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run: aws configure"
        exit 1
    fi
    
    # Check API key
    if [ -z "$LITELLM_API_KEY" ]; then
        if [ -f ../.env ]; then
            export $(grep LITELLM_API_KEY ../.env | xargs)
        fi
        if [ -z "$LITELLM_API_KEY" ]; then
            log_error "LITELLM_API_KEY not set. Export it or add to .env file"
            exit 1
        fi
    fi
    
    log_success "All prerequisites met!"
}

# ============ GET AWS ACCOUNT INFO ============
get_aws_info() {
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
    log_info "AWS Account: ${AWS_ACCOUNT_ID}"
    log_info "ECR URI: ${ECR_URI}"
}

# ============ FIRST-TIME SETUP ============
setup_aws_resources() {
    log_info "Setting up AWS resources (first-time)..."
    
    # Create ECR repository
    log_info "Creating ECR repository..."
    aws ecr create-repository \
        --repository-name ${ECR_REPO_NAME} \
        --region ${AWS_REGION} \
        --image-scanning-configuration scanOnPush=true \
        2>/dev/null || log_warn "ECR repository already exists"
    
    # Create ECS cluster
    log_info "Creating ECS cluster..."
    aws ecs create-cluster \
        --cluster-name ${ECS_CLUSTER_NAME} \
        --region ${AWS_REGION} \
        --capacity-providers FARGATE FARGATE_SPOT \
        --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
        2>/dev/null || log_warn "ECS cluster already exists"
    
    # Create CloudWatch log group
    log_info "Creating CloudWatch log group..."
    aws logs create-log-group \
        --log-group-name /ecs/${TASK_FAMILY} \
        --region ${AWS_REGION} \
        2>/dev/null || log_warn "Log group already exists"
    
    # Create IAM role for ECS task execution
    log_info "Creating IAM roles..."
    
    # Task execution role (for pulling images, logging)
    cat > /tmp/ecs-trust-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
EOF
    
    aws iam create-role \
        --role-name birdsense-ecs-execution-role \
        --assume-role-policy-document file:///tmp/ecs-trust-policy.json \
        2>/dev/null || log_warn "Execution role already exists"
    
    aws iam attach-role-policy \
        --role-name birdsense-ecs-execution-role \
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy \
        2>/dev/null || true
    
    # Create VPC and subnets if needed (or use default VPC)
    log_info "Using default VPC..."
    DEFAULT_VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region ${AWS_REGION})
    
    if [ "$DEFAULT_VPC_ID" == "None" ]; then
        log_error "No default VPC found. Please create one or specify VPC ID."
        exit 1
    fi
    
    log_info "Default VPC: ${DEFAULT_VPC_ID}"
    
    # Get subnets
    SUBNET_IDS=$(aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=${DEFAULT_VPC_ID}" \
        --query "Subnets[*].SubnetId" \
        --output text \
        --region ${AWS_REGION} | tr '\t' ',')
    
    log_info "Subnets: ${SUBNET_IDS}"
    
    # Create security group
    log_info "Creating security group..."
    SG_ID=$(aws ec2 create-security-group \
        --group-name birdsense-sg \
        --description "BirdSense ECS Security Group" \
        --vpc-id ${DEFAULT_VPC_ID} \
        --region ${AWS_REGION} \
        --query "GroupId" \
        --output text 2>/dev/null) || SG_ID=$(aws ec2 describe-security-groups \
            --filters "Name=group-name,Values=birdsense-sg" \
            --query "SecurityGroups[0].GroupId" \
            --output text \
            --region ${AWS_REGION})
    
    # Add inbound rules
    aws ec2 authorize-security-group-ingress \
        --group-id ${SG_ID} \
        --protocol tcp \
        --port 7860 \
        --cidr 0.0.0.0/0 \
        --region ${AWS_REGION} 2>/dev/null || true
    
    aws ec2 authorize-security-group-ingress \
        --group-id ${SG_ID} \
        --protocol tcp \
        --port 8000 \
        --cidr 0.0.0.0/0 \
        --region ${AWS_REGION} 2>/dev/null || true
    
    log_info "Security Group: ${SG_ID}"
    
    # Store config for later use
    mkdir -p ~/.birdsense
    cat > ~/.birdsense/aws-config.env << EOF
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID}
AWS_REGION=${AWS_REGION}
ECR_URI=${ECR_URI}
DEFAULT_VPC_ID=${DEFAULT_VPC_ID}
SUBNET_IDS=${SUBNET_IDS}
SECURITY_GROUP_ID=${SG_ID}
EOF
    
    log_success "AWS setup complete! Config saved to ~/.birdsense/aws-config.env"
}

# ============ BUILD AND PUSH DOCKER IMAGE ============
build_and_push() {
    log_info "Building Docker image..."
    cd "$(dirname "$0")/.."
    
    # Build image
    docker build -t ${ECR_REPO_NAME}:latest .
    
    # Tag for ECR
    docker tag ${ECR_REPO_NAME}:latest ${ECR_URI}:latest
    docker tag ${ECR_REPO_NAME}:latest ${ECR_URI}:$(date +%Y%m%d-%H%M%S)
    
    # Login to ECR
    log_info "Logging into ECR..."
    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
    
    # Push image
    log_info "Pushing image to ECR..."
    docker push ${ECR_URI}:latest
    
    log_success "Image pushed to ${ECR_URI}:latest"
}

# ============ CREATE/UPDATE TASK DEFINITION ============
create_task_definition() {
    log_info "Creating ECS task definition..."
    
    # Load config
    source ~/.birdsense/aws-config.env
    
    # Create task definition JSON
    cat > /tmp/task-definition.json << EOF
{
    "family": "${TASK_FAMILY}",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "${CPU}",
    "memory": "${MEMORY}",
    "executionRoleArn": "arn:aws:iam::${AWS_ACCOUNT_ID}:role/birdsense-ecs-execution-role",
    "containerDefinitions": [
        {
            "name": "birdsense",
            "image": "${ECR_URI}:latest",
            "essential": true,
            "portMappings": [
                {
                    "containerPort": 7860,
                    "hostPort": 7860,
                    "protocol": "tcp"
                },
                {
                    "containerPort": 8000,
                    "hostPort": 8000,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {"name": "RUN_MODE", "value": "${RUN_MODE}"},
                {"name": "PYTHONUNBUFFERED", "value": "1"}
            ],
            "secrets": [
                {
                    "name": "LITELLM_API_KEY",
                    "valueFrom": "arn:aws:ssm:${AWS_REGION}:${AWS_ACCOUNT_ID}:parameter/birdsense/litellm-api-key"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/${TASK_FAMILY}",
                    "awslogs-region": "${AWS_REGION}",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "healthCheck": {
                "command": ["CMD-SHELL", "curl -f http://localhost:7860/ || curl -f http://localhost:8000/health || exit 1"],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 60
            }
        }
    ]
}
EOF
    
    # Register task definition
    aws ecs register-task-definition \
        --cli-input-json file:///tmp/task-definition.json \
        --region ${AWS_REGION}
    
    log_success "Task definition created: ${TASK_FAMILY}"
}

# ============ STORE API KEY IN SSM ============
store_api_key() {
    log_info "Storing API key in AWS SSM Parameter Store..."
    
    aws ssm put-parameter \
        --name "/birdsense/litellm-api-key" \
        --type "SecureString" \
        --value "${LITELLM_API_KEY}" \
        --overwrite \
        --region ${AWS_REGION}
    
    log_success "API key stored in SSM"
}

# ============ CREATE/UPDATE ECS SERVICE ============
deploy_service() {
    log_info "Deploying ECS service..."
    
    # Load config
    source ~/.birdsense/aws-config.env
    
    # Convert subnet IDs to JSON array
    SUBNET_JSON=$(echo $SUBNET_IDS | sed 's/,/","/g' | sed 's/^/["/' | sed 's/$/"]/')
    
    # Check if service exists
    SERVICE_EXISTS=$(aws ecs describe-services \
        --cluster ${ECS_CLUSTER_NAME} \
        --services ${ECS_SERVICE_NAME} \
        --region ${AWS_REGION} \
        --query "services[?status=='ACTIVE'].serviceName" \
        --output text 2>/dev/null)
    
    if [ -z "$SERVICE_EXISTS" ]; then
        # Create new service
        log_info "Creating new ECS service..."
        aws ecs create-service \
            --cluster ${ECS_CLUSTER_NAME} \
            --service-name ${ECS_SERVICE_NAME} \
            --task-definition ${TASK_FAMILY} \
            --desired-count 1 \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=${SUBNET_JSON},securityGroups=[\"${SECURITY_GROUP_ID}\"],assignPublicIp=ENABLED}" \
            --region ${AWS_REGION}
    else
        # Update existing service
        log_info "Updating existing ECS service..."
        aws ecs update-service \
            --cluster ${ECS_CLUSTER_NAME} \
            --service ${ECS_SERVICE_NAME} \
            --task-definition ${TASK_FAMILY} \
            --force-new-deployment \
            --region ${AWS_REGION}
    fi
    
    log_success "Service deployed!"
    
    # Wait for service to be stable
    log_info "Waiting for service to become stable (this may take 2-3 minutes)..."
    aws ecs wait services-stable \
        --cluster ${ECS_CLUSTER_NAME} \
        --services ${ECS_SERVICE_NAME} \
        --region ${AWS_REGION}
    
    log_success "Service is now running!"
}

# ============ GET SERVICE URL ============
get_service_url() {
    log_info "Getting service URL..."
    
    # Get task ARN
    TASK_ARN=$(aws ecs list-tasks \
        --cluster ${ECS_CLUSTER_NAME} \
        --service-name ${ECS_SERVICE_NAME} \
        --region ${AWS_REGION} \
        --query "taskArns[0]" \
        --output text)
    
    if [ "$TASK_ARN" == "None" ] || [ -z "$TASK_ARN" ]; then
        log_warn "No running tasks found. Service may still be starting."
        return
    fi
    
    # Get ENI ID
    ENI_ID=$(aws ecs describe-tasks \
        --cluster ${ECS_CLUSTER_NAME} \
        --tasks ${TASK_ARN} \
        --region ${AWS_REGION} \
        --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" \
        --output text)
    
    # Get public IP
    PUBLIC_IP=$(aws ec2 describe-network-interfaces \
        --network-interface-ids ${ENI_ID} \
        --region ${AWS_REGION} \
        --query "NetworkInterfaces[0].Association.PublicIp" \
        --output text)
    
    echo ""
    echo "========================================"
    echo -e "${GREEN}🐦 BirdSense is running!${NC}"
    echo "========================================"
    echo ""
    
    if [ "$RUN_MODE" == "api" ]; then
        echo "REST API: http://${PUBLIC_IP}:8000"
        echo "API Docs: http://${PUBLIC_IP}:8000/docs"
    elif [ "$RUN_MODE" == "both" ]; then
        echo "Web UI:   http://${PUBLIC_IP}:7860"
        echo "REST API: http://${PUBLIC_IP}:8000"
        echo "API Docs: http://${PUBLIC_IP}:8000/docs"
    else
        echo "Web UI:   http://${PUBLIC_IP}:7860"
    fi
    echo ""
}

# ============ MAIN ============
main() {
    echo ""
    echo "🐦 BirdSense AWS Deployment"
    echo "==========================="
    echo "Region: ${AWS_REGION}"
    echo "Mode: ${RUN_MODE}"
    echo ""
    
    check_prerequisites
    get_aws_info
    
    if [ "$SETUP_MODE" = true ]; then
        setup_aws_resources
        store_api_key
    fi
    
    # Load config if exists
    if [ -f ~/.birdsense/aws-config.env ]; then
        source ~/.birdsense/aws-config.env
    else
        log_error "AWS config not found. Run with --setup first."
        exit 1
    fi
    
    build_and_push
    create_task_definition
    deploy_service
    get_service_url
}

main "$@"

