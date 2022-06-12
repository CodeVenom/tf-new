import glob
import os
import sys
import yaml

from jinja2 import Environment, FileSystemLoader


class Renderer:
    def __init__(self):
        self.config = {
            'global': {},
        }
        self.envs = {
            'template': Environment(loader=FileSystemLoader('templates')),
            'text': Environment(),
        }
        with open('config/global.yml', 'r') as f:
            self.config['global'] = yaml.safe_load(f)['global']

    # - - - - - actions - - - - -
    def process(self, module_dir):
        # TODO: append backslash to dir if needed
        # TODO: check existence of dir
        context = {}
        values = {}

        current_environment = Environment(loader=FileSystemLoader(module_dir))
        # TODO: probably will rename files to .tf.j2
        terraform_template_files = glob.glob(module_dir + '*.tf')

        with open(module_dir + 'module.yml', 'r') as module_config_file:
            context = yaml.safe_load(module_config_file)
            # print(context['context'])
        for account in self.config['global']['accounts']:
            account_dir = module_dir + account['name'] + '/'
            os.makedirs(account_dir, exist_ok=True)

            # TODO: define function for values preparation
            context['context']['account'] = account
            values = self.config | context

            with open(account_dir + 'backend.tf', 'w') as terraform_result_file:
                terraform_result_file.write(
                    self.template(key='backend.tf.j2').render(values=values)
                )

            for terraform_template_file in terraform_template_files:
                terraform_file_name = terraform_template_file.split('/')[-1]
                with open(account_dir + terraform_file_name, 'w') as terraform_result_file:
                    terraform_result_file.write(
                        current_environment.get_template(terraform_file_name).render(values=values)
                    )

    # - - - - - simple helpers - - - - -
    def template(self, key, template_type='template'):
        return self.envs[template_type].get_template(key)


if __name__ == '__main__':
    renderer = Renderer()
    sys.exit(renderer.process('live/chair/'))
