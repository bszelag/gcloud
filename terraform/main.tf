terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    # google-beta = {
    #   source  = "hashicorp/google-beta"
    #   version = "~> 4.0"
    # }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# provider "google-beta" {
#   project = var.project_id
#   region  = var.region
#   zone    = var.zone
# }

resource "google_project_service" "required_apis" {
  for_each = toset([
    "container.googleapis.com",
    "sqladmin.googleapis.com",

    "containerregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "compute.googleapis.com",
    "iam.googleapis.com",
    "servicenetworking.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "secretmanager.googleapis.com"
  ])

  project = var.project_id
  service = each.value

  disable_dependent_services = true
  disable_on_destroy         = false
}

resource "google_compute_network" "vpc" {
  name                    = "birthday-api-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.required_apis]
}

resource "google_compute_subnetwork" "gke_subnet" {
  name          = "birthday-api-gke-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
}

resource "google_compute_subnetwork" "sql_subnet" {
  name          = "birthday-api-sql-subnet"
  ip_cidr_range = "10.1.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
  purpose       = "PRIVATE_SERVICE_CONNECTION"
}

resource "google_compute_global_address" "private_ip_address" {
  name          = "birthday-api-private-ip"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# Cloud Router for NAT Gateway
resource "google_compute_router" "router" {
  name    = "birthday-api-router"
  region  = var.region
  network = google_compute_network.vpc.id
}

# External IP for NAT Gateway
resource "google_compute_address" "nat_ip" {
  name   = "birthday-api-nat-ip"
  region = var.region
}

# NAT Gateway for private nodes to access internet
resource "google_compute_router_nat" "nat" {
  name                               = "birthday-api-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "MANUAL_ONLY"
  nat_ips                            = [google_compute_address.nat_ip.self_link]
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

resource "google_compute_firewall" "gke_nodes" {
  name    = "birthday-api-gke-nodes"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["10250", "443", "8080", "8081", "9090", "3000"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.0.0.0/24"]
  target_tags   = ["gke-node"]
}

# Allow all internal pod-to-pod communication
resource "google_compute_firewall" "gke_pod_communication" {
  name    = "birthday-api-pod-communication"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  source_ranges = ["10.0.0.0/24"]
  target_tags   = ["gke-node"]
}

resource "google_compute_firewall" "gke_master" {
  name    = "birthday-api-gke-master"
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }

  source_ranges = [var.authorized_networks]
  target_tags   = ["gke-master"]
}

resource "google_container_cluster" "primary" {
  name     = "birthday-api-cluster"
  location = var.region

  remove_default_node_pool = true
  initial_node_count       = 1

  deletion_protection = false

  network    = google_compute_network.vpc.id
  subnetwork = google_compute_subnetwork.gke_subnet.id

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = var.authorized_networks
      display_name = "My IP"
    }
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Temporarily disable network policy to avoid connectivity issues
  # network_policy {
  #   enabled = true
  # }

  depends_on = [
    google_project_service.required_apis,
    google_service_networking_connection.private_vpc_connection,
    google_compute_router_nat.nat
  ]
}

# GKE Node Pool
resource "google_container_node_pool" "primary_nodes" {
  name       = "birthday-api-node-pool"
  location   = google_container_cluster.primary.location
  cluster    = google_container_cluster.primary.name
  node_count = var.node_count

  autoscaling {
    min_node_count = var.min_node_count
    max_node_count = var.max_node_count
  }

  node_config {

    oauth_scopes = [
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
      "https://www.googleapis.com/auth/devstorage.read_only"
    ]

    labels = {
      env = var.environment
    }

    tags = ["gke-node"]

    machine_type = var.machine_type
    disk_size_gb = var.node_disk_size_gb
    disk_type    = var.node_disk_type

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }

  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }
}

resource "google_sql_database_instance" "main" {
  name             = "birthday-api-sql"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = var.sql_tier

    backup_configuration {
      enabled                        = true
      start_time                     = "02:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 7
      }
    }

    maintenance_window {
      day          = 7
      hour         = 2
      update_track = "stable"
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }

    user_labels = {
      environment = var.environment
      project     = "birthday-api"
    }
  }

  deletion_protection = false # normally it would be true, but since it's not a real production database, we want to delete it eventually

  depends_on = [
    google_project_service.required_apis,
    google_service_networking_connection.private_vpc_connection
  ]
}

resource "google_sql_database" "database" {
  name     = "birthday_api"
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "users" {
  name     = "birthday_user"
  instance = google_sql_database_instance.main.name
  password = random_password.database_password.result
}



# this could be used for deploy automation, but it's not currently set up
# Cloud Build Trigger
# resource "google_cloudbuild_trigger" "build_trigger" {
#   name        = "birthday-api-build"
#   description = "Build and deploy Birthday API"
#   location    = var.region

#   github {
#     owner = var.github_owner
#     name  = var.github_repo
#     push {
#       branch = "main"
#     }
#   }

#   filename = "cloudbuild.yaml"

#   depends_on = [google_project_service.required_apis]
# }

resource "google_service_account" "gke_service_account" {
  account_id   = "birthday-api-gke-sa"
  display_name = "Birthday API Service Account"
}

resource "google_service_account" "eso_service_account" {
  account_id                   = "birthday-api-eso-sa"
  display_name                 = "External Secrets Operator Service Account"
  create_ignore_already_exists = true
}

resource "google_service_account" "registry_service_account" {
  account_id                   = "birthday-api-registry-sa"
  display_name                 = "Registry Service Account"
  create_ignore_already_exists = true
}

resource "google_project_iam_member" "gke_service_account_roles" {
  for_each = toset([
    "roles/container.nodeServiceAccount",
    "roles/logging.logWriter",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/secretmanager.secretAccessor",
    "roles/cloudsql.client",
    "roles/artifactregistry.reader",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.gke_service_account.email}"
}

resource "google_project_iam_member" "registry_service_account_roles" {
  for_each = toset([
    "roles/artifactregistry.reader",
    "roles/artifactregistry.writer",
    "roles/iam.serviceAccountTokenCreator",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.registry_service_account.email}"
}

resource "google_project_iam_member" "eso_service_account_roles" {
  for_each = toset([
    "roles/secretmanager.secretAccessor",
    "roles/iam.serviceAccountTokenCreator"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.eso_service_account.email}"
}

# Allow the ESO service account to act as itself (needed for Workload Identity)
resource "google_service_account_iam_member" "eso_workload_identity" {
  service_account_id = google_service_account.eso_service_account.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[external-secrets/external-secrets]"
}

# Allow the application service account to act as the GKE service account (needed for Cloud SQL)
resource "google_service_account_iam_member" "app_workload_identity" {
  service_account_id = google_service_account.gke_service_account.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[birthday-api/birthday-api-sa]"
}

resource "random_password" "database_password" {
  length  = 16
  special = false
  upper   = true
  lower   = true
  numeric = true
}

resource "random_password" "secret_key" {
  length  = 32
  special = false
  upper   = true
  lower   = true
  numeric = true
}

resource "random_password" "grafana_admin_password" {
  length  = 16
  special = false
  upper   = true
  lower   = true
  numeric = true
}


resource "google_secret_manager_secret" "database_password" {
  secret_id = "birthday-api-db-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "database_password" {
  secret      = google_secret_manager_secret.database_password.id
  secret_data = random_password.database_password.result
}

resource "google_secret_manager_secret" "secret_key" {
  secret_id = "birthday-api-secret-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "secret_key" {
  secret      = google_secret_manager_secret.secret_key.id
  secret_data = random_password.secret_key.result
}

resource "google_secret_manager_secret" "grafana_admin_password" {
  secret_id = "birthday-api-grafana-admin-password"

  replication {
    auto {}
  }

  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "grafana_admin_password" {
  secret      = google_secret_manager_secret.grafana_admin_password.id
  secret_data = random_password.grafana_admin_password.result
}

resource "google_artifact_registry_repository" "repository" {
  location      = "europe"
  repository_id = "birthday-api-repository"
  description   = "Docker repository for birthday API"
  format        = "Docker"
}

# Budget alert for cost monitoring - not working, but would be useful
# resource "google_billing_budget" "budget" {
#   billing_account = var.billing_account
#   display_name    = "Birthday API Budget"

#   budget_filter {
#     projects = ["projects/${var.project_id}"]
#   }

#   amount {
#     specified_amount {
#       currency_code = "USD"
#       units         = "20" # $20 monthly budget
#     }
#   }

#   threshold_rules {
#     threshold_percent = 0.75 # Alert at 75%
#   }

#   threshold_rules {
#     threshold_percent = 1.0 # Alert at 100%
#   }
# }


# -----------------------------------------------------------------------------------
# Outputs
output "cluster_name" {
  value = google_container_cluster.primary.name
}

output "cluster_location" {
  value = google_container_cluster.primary.location
}

output "database_instance_name" {
  value = google_sql_database_instance.main.name
}

output "database_connection_name" {
  value = google_sql_database_instance.main.connection_name
}

output "database_password" {
  value     = random_password.database_password.result
  sensitive = true
}

output "secret_key" {
  value     = random_password.secret_key.result
  sensitive = true
}

output "grafana_admin_password" {
  value     = random_password.grafana_admin_password.result
  sensitive = true
}

output "eso_service_account_email" {
  value = google_service_account.eso_service_account.email
}

output "registry_service_account_email" {
  value = google_service_account.registry_service_account.email
}

output "registry_location" {
  value = google_artifact_registry_repository.repository.location
}

output "artifact_registry_repository" {
  value = google_artifact_registry_repository.repository.repository_id
}

output "project_id" {
  value = var.project_id
}
