variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "Target deployment region"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "Virtual Private Cloud range"
}

variable "db_username" {
  type        = string
  default     = "postgres"
  description = "PostgreSQL database master user"
}

variable "db_password" {
  type        = string
  default     = "secureflowpassword123"
  description = "PostgreSQL database master password"
  sensitive   = true
}
