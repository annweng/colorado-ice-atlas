output "project_name" {
  value = var.project_name
}

output "cloudflare_pages_project" {
  value       = try(module.cloudflare_free[0].pages_project_name, null)
  description = "Null until enable_cloudflare is true."
}
