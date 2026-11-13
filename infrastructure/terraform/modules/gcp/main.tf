terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.10"
    }
  }
}

variable "project_id" { type = string }
variable "region" { type = string }
variable "project_name" { type = string }

# Future Cloud Run / Cloud SQL / Cloud Storage wiring. Count is 0 at the root
# so these resources are not created until a GCP migration is approved.
output "run_service_name" {
  value = "${var.project_name}-api"
}

output "sql_instance_name" {
  value = "${var.project_name}-postgis"
}

output "bucket_name" {
  value = "${var.project_id}-${var.project_name}"
}
