output "vpc_id" {
  value       = aws_vpc.secureflow_vpc.id
  description = "Created VPC Identifier"
}

output "rds_endpoint" {
  value       = aws_db_instance.rds_postgres.endpoint
  description = "Database connection string address"
}

output "redis_endpoint" {
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
  description = "Redis endpoint node IP address"
}
