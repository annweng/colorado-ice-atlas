variable "cloudflare_api_token" {
  type      = string
  default   = ""
  sensitive = true
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token != "" ? var.cloudflare_api_token : "unconfigured"
}

provider "aws" {
  region                      = "us-west-2"
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
  access_key                  = "unconfigured"
  secret_key                  = "unconfigured"
}

provider "google" {
  project = "unconfigured"
  region  = "us-central1"
}
