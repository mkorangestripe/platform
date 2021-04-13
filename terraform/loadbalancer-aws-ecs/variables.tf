variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-2"
}

variable "aws_availability_zone" {
  description = "AWS availability zone"
  type        = string
  default     = "us-east-2a"
}

variable "aws_cloudwatch_log_group" {
  description = "AWS Cloudwatch log group"
  type        = string
  default     = "ecs/loadbalancer-app2"
}

variable "vpc_cidr_block" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}