# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
  name: main_solo
  author: evgeny.nifontov.extern@dvag.com
  version_added: "0.1" 
  short_description: get file from solo/ dir in main branch
  description:
      - This lookup returns content from main branch solo/ dir
  options:
    _terms:
      description: file_name
      required: True
  notes:
    - notes
"""
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

display = Display()

import requests
from requests.exceptions import HTTPError
from requests.auth import HTTPBasicAuth
import os
import inspect
import sys

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
parent_parent_dir = os.path.dirname(parent_dir)
python_lib_dir = os.path.join(parent_parent_dir, 'module_utils')
sys.path.insert(0, python_lib_dir) 

from dvag_foreman_api import ForemanAPI
from dvag_functions import struct_to_yaml

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

      # First of all populate options,
      # this will already take into account env vars and ini config
      self.set_options(var_options=variables, direct=kwargs)

      # lookups in general are expected to both take a list as input and output a list
      # this is done so they work with the looping construct 'with_'.
      ret = []

      foreman_server = 'foreman01.1.mgmt.dvag.net'

      try:
          foreman = ForemanAPI(
              verbose=False,
              server=foreman_server,
              validate_certs=True,
              katello=False
          )
          ans = foreman.get(url=f'hosts/1/parameters', params={'show_hidden': 'true'})

          if ans['status_code'] != 200:
              raise Exception(f"ERROR: {ans['error']}")

          main_solo_password = None

          foreman_host_parameters = ans['data']['results']
          for param in foreman_host_parameters:
              if param['name'] == 'main_solo_password':
                  main_solo_password = param['value']

          if main_solo_password is None:
            raise Exception(f"ERROR!! could not find main_solo_password parameter")

      except Exception as err:
        raise AnsibleError(f"ERROR!! could not find main_solo_password parameter")

      for term in terms:
          display.debug("lookup term: %s" % term)

          url = f'https://{foreman_server}/main_solo/{term}'
          user = 'main_solo'

          resp = None

          try:
              auth = HTTPBasicAuth(user, main_solo_password)
              resp = requests.get(url=url, auth=auth)
              resp.raise_for_status()
              data = resp.text

          except Exception as err:
            raise AnsibleError(f"ERROR getting <{term}>: {err}\n")

          ret.append(data)

          # consume an option: if this did something useful, you can retrieve the option value here

      return ret
