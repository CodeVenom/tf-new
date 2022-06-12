resource "aws_s3_bucket" "this" {
  bucket = "{{ values.context.account.name }}-super-awesome-bucket"
}
