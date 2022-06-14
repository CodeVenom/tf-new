# foo{{ values.context.set.foo }}!!!
# comment: {{ values.context.set.comment }}!!!
module "this" {
  source = "../../../modules/s3/{{ values.context.set.s3_submodule_version }}"

  bucket_name = "{{ values.context.account.name }}-{{ values.context.module.name }}-bucket"
}
