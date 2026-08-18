output "instance_public_ip" {
  value = aws_instance.app.public_ip
}

output "ssh_command" {
  value = "ssh -i ssh-keys/${var.student_name}-key.pem ubuntu@${aws_instance.app.public_ip}"
}

output "app_url" {
  value = "http://${aws_instance.app.public_ip}"
}
