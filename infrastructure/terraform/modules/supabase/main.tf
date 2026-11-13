# Supabase does not expose a complete official Terraform provider for PostGIS
# project creation on the free tier. Provision the project in the Supabase
# dashboard, enable the PostGIS extension, then supply DATABASE_URL to the app.
#
# This module documents the required outputs so a later provider can be dropped in.

variable "project_name" {
  type    = string
  default = "colorado-ice-atlas"
}

output "notes" {
  value = "Create a Supabase project manually, enable PostGIS, run database/migrations/001_init.sql, and set DATABASE_URL."
}
