# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
  name: dvaga_group_id
  author: evgeny.nifontov.extern@dvag.com
  version_added: "0.1" 
  short_description: get gid from dvag_conf/group_id.yml
  description:
      - This lookup returns tuid from dvag_conf/group_id.yml
  options:
    _terms:
      description: user name
      required: True
  notes:
    - notes
"""
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display
from azure.identity import DefaultAzureCredential, ClientSecretCredential, AzureCliCredential, DeviceCodeCredential
from azure.keyvault.secrets import SecretClient
import yaml
from yaml.loader import SafeLoader

display = Display()

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

      # First of all populate options,
      # this will already take into account env vars and ini config
      self.set_options(var_options=variables, direct=kwargs)

      # lookups in general are expected to both take a list as input and output a list
      # this is done so they work with the looping construct 'with_'.
      ret = []

      group_id_file = 'dvag_conf/group_id.yml'

      try:

        with open(group_id_file) as f:
          uid_data = yaml.load(f, Loader=SafeLoader)

      except Exception as err:
        raise AnsibleError(f"ERROR parsing yaml file  <{group_id_file}>: {err}")

      for term in terms:
          display.debug("lookup term: %s" % term)

          try:
            uid = uid_data[term]
          except Exception as err:
            raise AnsibleError(f"ERROR getting gid for group <{term}> from <{group_id_file}>: {err}")

          ret.append(uid)

          # consume an option: if this did something useful, you can retrieve the option value here

      return ret