resource "aws_s3_bucket" "this" {
  bucket = "{{ values.context.account.name }}-{{ values.context.module.name }}-bucket"
}
