terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
  }
}

variable "region" { type = string }
variable "project_name" { type = string }

# Future ECS Fargate / RDS PostGIS / S3 wiring. Disabled at the root module.
output "cluster_name" {
  value = "${var.project_name}-api"
}

output "bucket_name" {
  value = "${var.project_name}-data"
}
