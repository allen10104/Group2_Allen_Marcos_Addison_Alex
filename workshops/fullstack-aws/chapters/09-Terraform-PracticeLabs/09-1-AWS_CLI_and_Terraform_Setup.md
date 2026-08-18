# AWS CLI & Terraform Setup Guide

This guide details the step-by-step process to install, configure, and verify both the AWS CLI and HashiCorp Terraform on your machine.

---

## 1. AWS CLI Setup

### Step 1: Download and Install
Download and run the installer for your operating system:
* **Documentation Link:** [AWS CLI Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

### Step 2: Verify Installation
Open Terminal or Command Prompt (`cmd.exe`) and confirm the installation was successful:

```bash
aws --version

```

### Step 3: Configure AWS Credentials

Run the configuration command in your terminal:

```bash
aws configure

```

Provide the requested information when prompted:

| Configuration Field | Value |
| --- | --- |
| **AWS Access Key ID** | *Enter your Access Key ID* |
| **AWS Secret Access Key** | *Enter your Secret Access Key* |
| **Default region name** | `us-east-1` |
| **Default output format** | `json` |

> ⚠️ **Security Note:** Never disclose or publicly commit your access keys. Keep them stored securely.

#### How to generate an Access Key:

1. Log into the AWS Browser GUI.
2. Click your profile icon in the top-right corner.
3. Select **Security Credentials**.
4. Scroll to **Access keys** and click **Create Access Key**.

### Step 4: Confirm Authentication

Verify that your credentials are functioning correctly by checking your AWS caller identity:

```bash
aws sts get-caller-identity

```

---

## 2. Terraform (IaC) Setup

### Step 1: Download and Install

Download the appropriate Terraform binary or package for your system:

* **Download Link:** [HashiCorp Terraform Install](https://developer.hashicorp.com/terraform/install)

### Step 2: Verify Installation

Check that Terraform was properly installed and added to your system path:

```bash
terraform --version

```

```

```