module "cloudflare_free" {
  source         = "./modules/cloudflare"
  count          = var.enable_cloudflare ? 1 : 0
  account_id     = var.cloudflare_account_id
  project_name   = var.project_name
  r2_bucket_name = "${var.project_name}-data"
}

module "gcp_future" {
  source       = "./modules/gcp"
  count        = 0
  project_id   = "unset"
  region       = "us-central1"
  project_name = var.project_name
}

module "aws_future" {
  source       = "./modules/aws"
  count        = 0
  region       = "us-west-2"
  project_name = var.project_name
}

output "architecture" {
  value = "Local and GitHub Actions by default. Set enable_cloudflare=true after creating a Cloudflare account to provision Pages and R2."
}
