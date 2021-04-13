data "template_file" "task_definition_template" {
  template = file("task-definitions/loadbalancer-app2.json.tpl")
  vars = {
    AWS_REGION = var.aws_region,
    AWS_CLOUDWATCH_LOG_GROUP = var.aws_cloudwatch_log_group
  }
}