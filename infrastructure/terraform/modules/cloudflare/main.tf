terraform {
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.40"
    }
  }
}

variable "account_id" {
  type = string
}

variable "project_name" {
  type = string
}

variable "r2_bucket_name" {
  type = string
}

resource "cloudflare_pages_project" "atlas" {
  account_id        = var.account_id
  name              = var.project_name
  production_branch = "main"
}

resource "cloudflare_r2_bucket" "data" {
  account_id = var.account_id
  name       = var.r2_bucket_name
  location   = "WNAM"
}

output "pages_project_name" {
  value = cloudflare_pages_project.atlas.name
}

output "r2_bucket_name" {
  value = cloudflare_r2_bucket.data.name
}
