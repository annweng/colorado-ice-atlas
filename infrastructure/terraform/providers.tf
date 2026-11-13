terraform {
  required_version = ">= 1.5.0"
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.40"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 6.10"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
  # Local state for bootstrap. Move to R2 after the bucket exists.
  # See infrastructure/terraform/README.md.
  backend "local" {
    path = "terraform.tfstate"
  }
}

variable "cloudflare_account_id" {
  type      = string
  default   = ""
  sensitive = true
}

variable "enable_cloudflare" {
  type    = bool
  default = false
}

variable "project_name" {
  type    = string
  default = "colorado-ice-atlas"
}
