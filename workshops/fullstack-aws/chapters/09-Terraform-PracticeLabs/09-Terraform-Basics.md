# 09-Terraform-PracticeLabs

## 🎯 Phase Goal
Automate the provisioning, management, and lifecycle of the **Bank Design** cloud infrastructure on AWS using HashiCorp Terraform as Infrastructure as Code (IaC).

## 🛠️ Concepts & Topics Covered
* **Terraform Fundamentals:** Declarative configuration syntax (HCL), providers, resources, variables, and outputs.
* **Core CLI Workflow:** `terraform init`, `terraform plan`, `terraform apply`, `terraform destroy`.
* **State Management:** Local state files vs. AWS S3 Remote State storage with DynamoDB state locking.
* **Modular Infrastructure:** Writing reusable modules for VPCs, EC2 application servers, S3 frontend buckets, and DocumentDB database instances.

## 📋 Module Roadmap & Tasks

### Step 1: Terraform Environment & Provider Setup
* Configure main Terraform files:
  ```text
  terraform/
  ├── main.tf          # Core infrastructure resources
  ├── variables.tf     # Configurable inputs (region, instance types, DB credentials)
  ├── outputs.tf       # Exported resource details (S3 URL, EC2 Public IP)
  └── terraform.tfvars # Environment variable assignments