# Terraform

The application runs locally and on GitHub Actions without applying Terraform.

`enable_cloudflare` defaults to **false** so `terraform plan` does not create paid or account-bound resources. Do not apply production changes from pull requests.

## Commands

```bash
cd infrastructure/terraform
terraform init
terraform fmt -check
terraform validate
terraform plan -var-file=environments/free/terraform.tfvars
# terraform apply is manual after review
```

## Bootstrap remote state on R2

1. Create an R2 bucket once in the Cloudflare dashboard (`cia-tfstate`).
2. Create an API token with R2 edit permission.
3. Replace the local backend with:

```hcl
backend "s3" {
  bucket                      = "cia-tfstate"
  key                         = "free/terraform.tfstate"
  region                      = "auto"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  skip_s3_checksum            = true
  endpoints = { s3 = "https://<accountid>.r2.cloudflarestorage.com" }
}
```

R2 does not provide native DynamoDB-style locking. Use a single operator for applies, or add a lock object convention documented in `docs/deployment.md`.

## Modules

| Module | Status |
| --- | --- |
| `modules/cloudflare` | Pages + R2, gated by `enable_cloudflare` |
| `modules/supabase` | Documentation only; create the project in the dashboard |
| `modules/gcp` | Future Cloud Run / Cloud SQL / GCS |
| `modules/aws` | Future ECS / RDS / S3 |
