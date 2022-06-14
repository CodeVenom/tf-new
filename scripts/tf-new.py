import copy
import glob
import os
import sys
import yaml

from jinja2 import Environment, FileSystemLoader


class Renderer:
    DEFAULT_BACKEND_TF = 'backend.tf'
    DEFAULT_MODULE_GROUP = 'all'

    SKELETON_CONTEXT_EXTRA = {
        'account': {},
        'group': {},
        'env': {},
    }

    def __init__(self):
        self.config = {
            'global': {},
        }
        self.envs = {
            'template': Environment(loader=FileSystemLoader('templates')),
            'text': Environment(),
        }
        self.load_global_config()
        self.shallow_groups = self.extract_groups()

    # - - - - - actions - - - - -
    def process(self, module_dir):
        # TODO: use more sophisticated logging here
        print('Info: processing ' + module_dir)
        module_dir = fix_dir(module_dir)
        if not os.path.isdir(module_dir):
            # TODO: use logging prefix?
            raise Exception(module_dir + ' does not exist')

        current_template_environment = Environment(loader=FileSystemLoader(module_dir))
        terraform_template_files = glob.glob(module_dir + '*.tf')
        module_config = self.load_module_config(module_dir)

        for account in self.config['global']['accounts']:
            context = copy.deepcopy(module_config)
            self.patch_transient_configs(
                module_config=context,
                account_data=account,
            )

            if not self.is_in_group(
                    group_key=context['context']['module']['group'],
                    account_name=account['name'],
            ):
                continue

            account_dir = fix_dir(module_dir + account['name'])
            os.makedirs(
                account_dir,
                exist_ok=True,
            )
            values = self.config | context

            with open(account_dir + 'backend.tf', 'w') as terraform_result_file:
                terraform_result_file.write(
                    self.template(key=context['context']['module']['backend_template']).render(values=values)
                )

            for terraform_template_file in terraform_template_files:
                terraform_file_name = terraform_template_file.split('/')[-1]
                with open(account_dir + terraform_file_name, 'w') as terraform_result_file:
                    terraform_result_file.write(
                        current_template_environment.get_template(terraform_file_name).render(values=values)
                    )

    def process_all(self, start_dir):
        module_dir_set = set()
        for directory, _, _ in os.walk(start_dir):
            directory = fix_dir(directory)
            if os.path.isfile(directory + 'module.tf.yml'):
                module_dir_set.add(directory)
        for module_dir in module_dir_set:
            self.process(module_dir)

    # - - - - - advanced helpers - - - - -
    def load_module_config(self, module_dir):
        module_dir = fix_dir(module_dir)
        module_config_file_path = module_dir + 'module.tf.yml'
        if not os.path.isfile(module_config_file_path):
            return None

        with open(module_config_file_path, 'r') as module_config_file:
            # TODO: use object instead of dict
            module_config = yaml.safe_load(module_config_file)
        module = module_config['context']['module']
        # default module name is the directory name
        if 'name' not in module:
            module['name'] = bottom_dir(module_dir)
        if 'backend_template' not in module:
            module['backend_template'] = self.DEFAULT_BACKEND_TF
        if 'group' not in module:
            module['group'] = self.DEFAULT_MODULE_GROUP
        return module_config

    def patch_transient_configs(self, module_config, account_data):
        account_key = account_data['name'].replace('-', '_')
        env = account_data['env']
        context = module_config['context']
        extra = context.get('extra', self.SKELETON_CONTEXT_EXTRA)

        if 'region_alt' not in account_data:
            account_data['region_alt'] = account_data['region']

        module_config['context']['account'] = account_data
        # most specific configuration takes precedence: env -> group -> account
        if env in extra['env']:
            context['set'] |= extra['env'][env]
        # TODO: merge group if present
        if account_key in extra['account']:
            context['set'] |= extra['account'][account_key]

    # - - - - - simple helpers - - - - -
    def is_in_group(self, group_key, account_name):
        return group_key in self.shallow_groups and account_name in self.shallow_groups[group_key]

    def template(self, key, template_type='template'):
        return self.envs[template_type].get_template(key)

    # - - - - - init helpers - - - - -
    def extract_groups(self):
        groups = self.config['global']['groups']
        shallow_groups = {}
        for group_key, group in groups.items():
            shallow_groups[group_key] = []
            for account_data in group:
                shallow_groups[group_key].append(account_data['name'])
        return shallow_groups

    def load_global_config(self):
        with open('config/global.yml', 'r') as f:
            global_config = yaml.safe_load(f)['global']
        # TODO: assert names are unique
        global_config['groups']['all'] = global_config['accounts']
        global_config['groups']['none'] = {}
        self.config['global'] = global_config


# - - - - - static helpers - - - - -
def fix_dir(path_string):
    if not path_string.endswith('/'):
        path_string += '/'
    return path_string


def bottom_dir(path_string):
    return fix_dir(path_string).split('/')[-2]


if __name__ == '__main__':
    selected_directory = None
    process_all = False
    renderer = Renderer()

    args = sys.argv[1:]
    if '--all' in args:
        args[args.index('--all')] = '-a'
    if '-a' in args:
        process_all = True
    if '--directory' in args:
        args[args.index('--directory')] = '-d'
    if '-d' in args:
        selected_directory = args[args.index('-d') + 1]

    if selected_directory:
        if process_all:
            renderer.process_all(selected_directory)
        else:
            renderer.process(selected_directory)
