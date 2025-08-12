# Terraform variables for Birthday API Infrastructure

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "The GCP zone for zonal resources"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "node_count" {
  description = "Number of nodes in the GKE cluster"
  type        = number
  default     = 2
}

variable "min_node_count" {
  description = "Minimum number of nodes in the GKE cluster"
  type        = number
  default     = 1
}

variable "max_node_count" {
  description = "Maximum number of nodes in the GKE cluster"
  type        = number
  default     = 3 # Reduced from 5 for cost optimization
}

variable "machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-small"
}

variable "sql_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"
}

# GitHub Configuration - this would be used for cloud build, which is not implemented
# variable "github_owner" {
#   description = "GitHub repository owner"
#   type        = string
#   default     = "bszelag"
# }

# variable "github_repo" {
#   description = "GitHub repository name"
#   type        = string
#   default     = "gcp-project"
# }

variable "authorized_networks" {
  description = "CIDR blocks for authorized network access to GKE master"
  type        = string
  default     = "127.0.0.1/0"
}

variable "node_disk_size_gb" {
  description = "Disk size in GB for GKE nodes"
  type        = number
  default     = 16
}

variable "node_disk_type" {
  description = "Disk type for GKE nodes"
  type        = string
  default     = "pd-standard"
}

variable "billing_account" {
  description = "GCP billing account ID"
  type        = string
}


