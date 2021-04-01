terraform {
  required_providers {
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

provider "docker" {}

resource "docker_image" "loadbalancer" {
  name         = "mkorangestripe/loadbalancer:latest"
  keep_locally = false
}

resource "docker_container" "loadbalancer" {
  image = docker_image.loadbalancer.latest
  name  = "cat_loadbalancer"
  ports {
    internal = 80
    external = 8000
  }
}
