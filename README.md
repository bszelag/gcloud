# gcloud

A simple HTTP API that manages user birthdays with two endpoints:

- `PUT /hello/<username>` - Save/update user's date of birth
- `GET /hello/<username>` - Get birthday message

## Quick Start

### Local Development

```bash
# Start development environment
./scripts/dev.sh start

# Docs
curl http://localhost:8000/docs

# Example curl to try it
curl -X 'PUT' \
  'http://localhost:8000/hello/alice' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -d '{
  "dateOfBirth": "2025-07-12"
}'

curl -X 'GET' \
  'http://localhost:8000/hello/alice' \
  -H 'accept: application/json'
```

### Production Deployment

```bash
# Deploy infrastructure
./scripts/deploy-infrastructure.sh apply

# Deploy application
./scripts/deploy-infrastructure.sh deploy
```

### Running tests
```bash
# Please use virtual env of your choice, with python 3.10.18
./scripts/test.sh
```

## Project Structure

- `app/` - application code
- `tests/` - tests
- `terraform/` - GCP infrastructure as code
- `helm/` - kubernetes helm chart
- `scripts/` - Deployment and management scripts
- `docker-compose.yml` - Local development environment

## Technologies

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Testing**: pytest
- **Infrastructure**: Terraform, GKE, Cloud SQL
- **Deployment**: Docker, Helm, Kubernetes
- **Secrets**: External Secrets Operator, GCP Secret Manager
- **Monitoring**: Prometheus, Grafana, Alertmanager

## Documentation

- [System Architecture](docs/system-architecture.md) - Comprehensive system diagram and component details

## Missing parts, possible improvements, features that are nice to have

- Current solution misses running properly alembic migrations that would create proper schema during 1st run

- Local development on local k3d/kind/minikube cluster
- Proper monitoring (customized alerts, monitoring external database)
- Proper scaling techniques
  - better hpa rules
  - or scaling using keda - to base on custom metrics
- Proper security hardening (gke cluster)
- Proper secure access to k8s cluster (rbac roles) for administrators/developers
- Add tests of the whole scenario - infrastructure creation and app deployment - as a part of CI
- Setting up CI/CD
  - I'd try cloud build (deploying it using terraform)
- Add disaster recovery plan
- Ensure deployment uses diffrent availability zones to prevent from zone outage
- Blue/green deployment or canary deployments for release process
- GKE terraform provider has an option to configure k8s deployment, maybe this could be used here (since it's simple app)
- Store tfstate in cloud - preferably in GCP
- Terraform cleanup: divide main.tf into smaller files
- Helm cleanup: separate app configs from external-secrets and from monitoring
- We could have a helm repository where we'd store helm chart definitions and then use them as dependencies
- If we'd like to assume we have already working environment where we'd like to deploy new versions of the app using CD we could use gitops approach - i.e using Flux
- Application could have proper load balancing, ingress with ipv6
- We could add domain creating to terraform and then use it in ingress definition (so that app would be accessible from the internet)
- Implementing proper set of network policies
- The more complex it gets we should have something better than shell scripts to do the deployment
