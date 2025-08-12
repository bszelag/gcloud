#!/bin/bash

set -e

show_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  init      - Initialize Terraform"
    echo "  plan      - Plan Terraform changes"
    echo "  apply     - Apply Terraform changes"
    echo "  destroy   - Destroy infrastructure"
    echo "  output    - Show Terraform outputs"
    echo "  push_image - Push image to Artifact Registry"
    echo "  configure_kubectl - Configure kubectl"
    echo "  deploy - Deploy application"
    echo "  help      - Show this help message"
}

check_prerequisites() {
    echo "Checking prerequisites..."
    
    if ! command -v gcloud &> /dev/null; then
        echo "Error: gcloud CLI is not installed"
        exit 1
    fi
    
    if ! command -v terraform &> /dev/null; then
        echo "Error: terraform is not installed"
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        echo "Error: kubectl is not installed"
        exit 1
    fi
    
    if ! command -v helm &> /dev/null; then
        echo "Error: helm is not installed"
        exit 1
    fi
    
    echo "Prerequisites check passed!"
}

check_auth() {
    echo "Checking authentication to GCP..."
    
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo "Error: Not authenticated with gcloud, run 'gcloud auth login'"
        exit 1
    fi
    
    if ! gcloud auth application-default print-access-token &> /dev/null; then
        echo "Error: Application default credentials not set, run 'gcloud auth application-default login'"
        exit 1
    fi
    
    echo "Authentication check passed!"
}

init_terraform() {
    echo "Initializing Terraform..."
    
    cd terraform
    
    if [ ! -f "terraform.tfvars" ]; then
        echo "Error: terraform.tfvars file not found, copy terraform.tfvars.example to terraform.tfvars and update the values"
        exit 1
    fi
    
    terraform init
    
    echo "Terraform initialized successfully!"
    cd ..
}

plan_terraform() {
    echo "Running terraform plan..."
    
    cd terraform
    rm -f tfplan
    terraform plan -out=tfplan
    cd ..
    
    echo "Terraform plan completed!"
}

apply_terraform() {
    echo "Applying Terraform changes..."
    
    cd terraform
    
    if [ ! -f "tfplan" ]; then
        echo "No Terraform plan found"
        echo "Running terraform apply"
        terraform apply
    else
        terraform apply tfplan
    fi
    echo "Terraform applied"
    cd ..
}

destroy_infrastructure() {
    echo "Destroying infrastructure..."
    
    read -p "Are you sure you want to destroy all infrastructure? If yes, answer what's the meaning of life: " confirm
    if [ "$confirm" != "42" ]; then
        echo "Destruction cancelled"
        exit 1
    fi
    
    cd terraform
    terraform destroy --auto-approve
    cd ..
    
    echo "Infrastructure destroyed successfully!"
}

configure_kubectl() {
    echo "Get kubectl context..."

    cd ./terraform
    CLUSTER_NAME=$(terraform output -raw cluster_name)
    CLUSTER_LOCATION=$(terraform output -raw cluster_location)
    PROJECT_ID=$(terraform output -raw project_id)
    cd ../

    gcloud container clusters get-credentials $CLUSTER_NAME --region $CLUSTER_LOCATION --project $PROJECT_ID
    
    echo "kubectl context set"
}

push_image() {
    echo "Building Docker image..."

    PROJECT_ID=$(terraform -chdir=terraform output -raw project_id 2>/dev/null || gcloud config get-value project)
    REPOSITORY=$(terraform -chdir=terraform output -raw artifact_registry_repository 2>/dev/null || echo "")
    LOCATION=$(terraform -chdir=terraform output -raw registry_location 2>/dev/null || echo "europe")

    docker build -t birthday-api .
    docker tag birthday-api ${LOCATION}-docker.pkg.dev/$PROJECT_ID/${REPOSITORY}/birthday-api:latest

    gcloud auth print-access-token | docker login \
    -u oauth2accesstoken \
    --password-stdin https://${LOCATION}-docker.pkg.dev

    docker push ${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/birthday-api:latest
    
}

deploy_application() {
    echo "Deploying application..."

    configure_kubectl

    echo "Getting Terraform outputs..."
    PROJECT_ID=$(terraform -chdir=terraform output -raw project_id 2>/dev/null || gcloud config get-value project)
    ESO_SERVICE_ACCOUNT=$(terraform -chdir=terraform output -raw eso_service_account_email 2>/dev/null || echo "")
    LOCATION=$(terraform -chdir=terraform output -raw registry_location 2>/dev/null || echo "europe")
    REPOSITORY=$(terraform -chdir=terraform output -raw artifact_registry_repository 2>/dev/null || echo "birthday-api-repository")
    CLUSTER_NAME=$(terraform -chdir=terraform output -raw cluster_name 2>/dev/null || echo "birthday-api-cluster")
    CLUSTER_LOCATION=$(terraform -chdir=terraform output -raw cluster_location 2>/dev/null || echo "europe-west4")
    DATABASE_CONNECTION_NAME=$(terraform -chdir=terraform output -raw database_connection_name 2>/dev/null || echo "")

    # push_image

    # kubectl create namespace birthday-api --dry-run=client -o yaml | kubectl apply -f -
    # kubectl create namespace external-secrets --dry-run=client -o yaml | kubectl apply -f -

    # helm repo add external-secrets https://charts.external-secrets.io
    # helm repo update
    
    # helm upgrade --install external-secrets external-secrets/external-secrets \
    #     --namespace external-secrets \
    #     --set installCRDs=true \
    #     --set serviceAccount.create=true \
    #     --set serviceAccount.name=external-secrets \
    #     --set serviceAccount.annotations."iam\.gke\.io/gcp-service-account"="$ESO_SERVICE_ACCOUNT" \
    #     --wait --timeout=10m

    # echo "Waiting for External Secrets Operator to be ready..."
    # kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=external-secrets -n external-secrets --timeout=300s

    # echo "Waiting for External Secrets CRDs to be available..."
    # kubectl wait --for=condition=established --timeout=60s crd/externalsecrets.external-secrets.io
    # kubectl wait --for=condition=established --timeout=60s crd/secretstores.external-secrets.io

    # echo "Verifying External Secrets CRDs are available..."
    # kubectl get crd externalsecrets.external-secrets.io
    # kubectl get crd secretstores.external-secrets.io

    # echo "Waiting a moment for CRDs to be fully registered..."
    # sleep 5

    echo "Updating Helm dependencies..."
    helm dependency update ./helm/birthday-api

    echo "Deploying application..."
    helm upgrade --install birthday-api ./helm/birthday-api \
        --namespace birthday-api \
        --set image.repository=${LOCATION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/birthday-api \
        --set image.tag=latest \
        --set externalSecrets.secretStore.enabled=true \
        --set externalSecrets.externalSecrets.enabled=true \
        --set externalSecrets.secretStore.projectID=$PROJECT_ID \
        --set externalSecrets.secretStore.clusterLocation=$CLUSTER_LOCATION \
        --set externalSecrets.secretStore.clusterName=$CLUSTER_NAME \
        --set externalSecrets.serviceAccount.enabled=false \
        --set database.connectionName=${DATABASE_CONNECTION_NAME} \
        --set database.cloudSqlProxy.enabled=true \
        --set database.name=birthday_api \
        --set database.user=birthday_user \
        --set database.migration.enabled=true \
        --set serviceAccount.annotations."iam\.gke\.io/gcp-service-account"="birthday-api-gke-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
        --set monitoring.enabled=true \
        --set kube-prometheus-stack.grafana.enabled=true \
        --set kube-prometheus-stack.prometheus.enabled=true \
        --set kube-prometheus-stack.alertmanager.enabled=true \
        --wait --timeout=20m
        
    echo "Application deployed successfully!"
}

# Main script logic
case "${1:-help}" in
    init)
        check_prerequisites
        check_auth
        init_terraform
        ;;
    plan)
        check_prerequisites
        check_auth
        init_terraform
        plan_terraform
        ;;
    apply)
        check_prerequisites
        check_auth
        init_terraform
        apply_terraform
        configure_kubectl
        ;;
    push_image)
        push_image
        ;;
    configure_kubectl)
        configure_kubectl
        ;;
    destroy)
        check_prerequisites
        check_auth
        destroy_infrastructure
        ;;
    output)
        cd terraform
        show_outputs
        cd ..
        ;;
    deploy)
        check_prerequisites
        check_auth
        deploy_application
        ;;
    help|*)
        show_usage
        ;;
esac
