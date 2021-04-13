[
  {
    "name": "cat-loadbalancer",
    "image": "mkorangestripe/loadbalancer:latest",
    "command": ["gunicorn -b 0.0.0.0:80 load_balancer:app"],
    "entryPoint": ["sh", "-c"],
    "essential": true,
    "portMappings": [
      {
        "containerPort": 80,
        "hostPort": 80
      }
    ],
    "memory": 512,
    "cpu": 256,
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "${AWS_CLOUDWATCH_LOG_GROUP}",
        "awslogs-region": "${AWS_REGION}",
        "awslogs-stream-prefix": "ecs"
      }
    }
  }
]