from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import requests
import sys
import os


DOCUMENTATION = r'''
    name: dvag_foreman_inventory
    plugin_type: inventory
    short_description: dynamic inventory dvag_foreman_inventory
    description: dynamic inventory dvag_foreman_inventory
    options:
      plugin:
          description: Name of the plugin
          required: true
          choices: ['dvag_foreman_inventory']
'''

from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.common.yaml
from ansible.plugins.inventory import BaseInventoryPlugin
from ansible.errors import AnsibleError, AnsibleParserError
import requests
from requests.exceptions import HTTPError
from requests.auth import HTTPBasicAuth
import re
import sys, traceback
from ansible.inventory.helpers import get_group_vars
from ansible.utils.vars import combine_vars
import yaml

import os
import inspect

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
parent_parent_dir = os.path.dirname(parent_dir)
python_lib_dir = os.path.join(parent_parent_dir, 'module_utils')
sys.path.insert(0, python_lib_dir)

inventory_cache_file_name = 'cache/dvag_foreman_inventory.yaml'

from dvag_foreman_api import ForemanAPI
from dvag_functions import struct_to_yaml

class InventoryModule(BaseInventoryPlugin):
    NAME = 'dvag_foreman_inventory'

    def verify_file(self, path):
        return True

    def template(self, host, expression, to_expr=False, to_bool=False):

        host_object = self.inventory.get_host(host)
        host_vars = host_object.get_vars()
        group_vars = get_group_vars( host_object.get_groups() )
        all_vars = combine_vars(group_vars, host_vars)

        self.templar.available_variables = all_vars
        if to_expr:
            use_expression = '{{ ' + expression + ' }}'
        else:
            use_expression = expression

        #print(f"use_expression=>>{use_expression}<<")
        res = self.templar.do_template(use_expression, fail_on_undefined=True)

        if to_bool:
            ret = (res == 'True')
        else:
            ret = res
        #print(f"type:{type(ret)} ret: {ret}")
        return ret

    def parse(self, inventory, loader, path, cache):
        super(InventoryModule, self).parse(inventory, loader, path, cache)

        try:

            config = self._read_config_data(path)

            self.VERBOSITY = int(os.getenv('VERBOSITY', '0'))
            self.ANSIBLE_SELECT = os.getenv('ANSIBLE_SELECT', None)
            self.DEBUG_HOST = os.getenv('DEBUG_HOST', '')
            self.ANSIBLE_USE_INVENTORY_FILE = os.getenv('ANSIBLE_USE_INVENTORY_FILE', '')

            foreman_server = config.get('foreman_server')
            foreman_validate_certs =  config.get('foreman_validate_certs')

            inventory_data_yaml = ''

            if self.ANSIBLE_USE_INVENTORY_FILE != '':
                if self.VERBOSITY >= 0:
                    print(f'get inventory from {self.ANSIBLE_USE_INVENTORY_FILE}')
                try:
                    with open(self.ANSIBLE_USE_INVENTORY_FILE, 'r') as inventory_file:
                        inventory_data_yaml = inventory_file.read()
                except Exception as err:
                    raise Exception(f"ERROR: reading {self.ANSIBLE_USE_INVENTORY_FILE}\n{err}\n")
            else:

                if foreman_validate_certs is None:
                    foreman_validate_certs = False

                foreman = ForemanAPI(
                    verbose=False,
                    server=foreman_server,
                    validate_certs=foreman_validate_certs,
                    katello=False
                )

                #foreman_host_id = foreman.get_id(url='hosts', search=f'''name="foreman01.1.mgmt.dvag.net"''')

                ans = foreman.get(url=f'hosts/1/parameters', params={'show_hidden': 'true'})

                if ans['status_code'] != 200:
                    raise Exception(f"ERROR: {ans['error']}")

                #print(struct_to_yaml(ans))

                dvag_inventory_password = None

                foreman_host_parameters = ans['data']['results']
                for param in foreman_host_parameters:
                    if param['name'] == 'dvag_inventory_password':
                        dvag_inventory_password = param['value']

                if dvag_inventory_password is None:
                    raise Exception(f"ERROR!! could not find dvag_inventory_password parameter")

                url = f'https://{foreman_server}/dvag_inventory/get_inventory'

                user = 'dvag_inventory'

                try:
                    if self.VERBOSITY >= 0:
                        print(f'get inventory from {url}')

                    auth = HTTPBasicAuth(user, dvag_inventory_password)
                    resp = requests.get(url=url, auth=auth)
                    #resp = requests.get(url=url, auth=auth, verify=False)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as err:
                    raise Exception(f"{err}\n{resp.text}\n")

                #print(struct_to_yaml(data))
                #sys.exit(0)
                if data['code'] != 200:
                    raise Exception(f"ERROR: responce code {data['code']} != 200: {struct_to_yaml(data)}")

                inventory_data_yaml = data['inventory_data']

                with open(inventory_cache_file_name, 'w') as inventory_cache:
                    inventory_cache.write(inventory_data_yaml)

            #print(dir(self.inventory))
            all_group = self.inventory.groups['all']
            self.inventory.add_group('selected_hosts')
            self.inventory.add_child('all', 'selected_hosts')

            inventory_data = yaml.safe_load_all(inventory_data_yaml)

            if config.get('only_add_variables_for_already_defined_hosts'):

                for server_data in inventory_data:

                    fqdn = server_data['name']
                    if self.DEBUG_HOST != '' and self.DEBUG_HOST != fqdn:
                        continue

                    if self.inventory.get_host(fqdn) is not None:

                        inventory_host = self.inventory.get_host(fqdn)

                        #print(dir(inventory_host))

                        self.inventory.set_variable(fqdn, 'fqdn', fqdn)
                        self.inventory.set_variable(fqdn, 'architecture', server_data['architecture_name'])
                        self.inventory.set_variable(fqdn, 'domain', server_data['domain_name'])
                        self.inventory.set_variable(fqdn, 'foreman_environment', server_data['environment_name'])
                        self.inventory.set_variable(fqdn, 'primary_ip', server_data['ip'])
                        self.inventory.set_variable(fqdn, 'ansible_host', server_data['ip'])
                        self.inventory.set_variable(fqdn, 'foreman_operatingsystem', server_data['operatingsystem_name'])
                        self.inventory.set_variable(fqdn, 'foreman_subnet', server_data['subnet_name'])
                        self.inventory.set_variable(fqdn, 'foreman_model', server_data['model_name'])
                        self.inventory.set_variable(fqdn, 'foreman_hostgroup', server_data['hostgroup_title'])

            else:

                for server_data in inventory_data:
                    #print(struct_to_yaml(server_data))

                    fqdn = server_data['name']
                    if self.DEBUG_HOST != '' and self.DEBUG_HOST != fqdn:
                        continue

                    hostgroup = server_data.get('hostgroup_title')

                    ansible_group = 'all'

                    if hostgroup is not None:
                        hostgroup_parts = hostgroup.split('/')
                        parent = 'all'
                        group = ''
                        for part in hostgroup_parts:
                            if parent == 'all':
                                group = part
                            else:
                                group = parent + '_' + part

                            if self.inventory.groups.get(group) is None:
                                self.inventory.add_group(group)
                                self.inventory.set_variable(group, 'group', group)
                                self.inventory.add_child(parent, group)

                            parent = group

                        ansible_group = group

                    self.inventory.add_host(fqdn, group=ansible_group)
                    self.inventory.set_variable(fqdn, 'fqdn', fqdn)
                    self.inventory.set_variable(fqdn, 'architecture', server_data['architecture_name'])
                    self.inventory.set_variable(fqdn, 'domain', server_data['domain_name'])
                    self.inventory.set_variable(fqdn, 'foreman_environment', server_data['environment_name'])
                    self.inventory.set_variable(fqdn, 'primary_ip', server_data['ip'])
                    self.inventory.set_variable(fqdn, 'ansible_host', server_data['ip'])
                    self.inventory.set_variable(fqdn, 'foreman_operatingsystem', server_data['operatingsystem_name'])
                    self.inventory.set_variable(fqdn, 'foreman_subnet', server_data['subnet_name'])
                    self.inventory.set_variable(fqdn, 'foreman_model', server_data['model_name'])
                    self.inventory.set_variable(fqdn, 'foreman_hostgroup', server_data['hostgroup_title'])

                if self.ANSIBLE_SELECT is not None:
                    selected = self.template(host=node, expression=self.ANSIBLE_SELECT, to_expr=True, to_bool=True)
                    #print(f"{node} {selected}")

                    if selected:
                        self.inventory.add_host(node, group='selected_hosts')

        except Exception as err:
            print(err)
            traceback.print_exc(file=sys.stdout)
            sys.exit(11)

        return True


