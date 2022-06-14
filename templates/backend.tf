terraform {
  required_version = "~> 1.2.2"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.18.0"
    }
  }

  backend "s3" {
    bucket         = "jjb-tf"
    dynamodb_table = "jjb-tf-lock"
    key            = "playground/{{ values.context.account.name }}-{{ values.context.module.name }}.tfstate"
    region         = "{{ values.context.account.region }}"
    role_arn       = "{{ values.context.account.role_arn }}"
  }
}

provider "aws" {
  region  = "{{ values.context.account.region }}"

  assume_role {
    role_arn     = "{{ values.context.account.role_arn }}"
#    session_name = "SESSION_NAME"
#    external_id  = "EXTERNAL_ID"
  }
}
