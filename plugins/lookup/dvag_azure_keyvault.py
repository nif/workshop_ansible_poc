# python 3 headers, required if submitting to Ansible
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
  name: dvag_azure_keyvault
  author: evgeny.nifontov.extern@dvag.com
  version_added: "0.1" 
  short_description: read secrtes from azure keyvault
  description:
      - This lookup returns the secrtet from azutre keyvault
  options:
    _terms:
      description: secret name(s) to read
      required: True
    keyvault_name:
      description:
        name of the azure keyvault
      type: string
      ini:
        - section: azure_keyvault_lookup
          key: keyvault_name
  notes:
    - notes
"""
from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display
from azure.identity import DefaultAzureCredential, ClientSecretCredential, AzureCliCredential, DeviceCodeCredential
from azure.keyvault.secrets import SecretClient

display = Display()

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

      # First of all populate options,
      # this will already take into account env vars and ini config
      self.set_options(var_options=variables, direct=kwargs)

      # lookups in general are expected to both take a list as input and output a list
      # this is done so they work with the looping construct 'with_'.
      ret = []

      keyvault_name = 'kv-bp-aufbau-01-prd'

      if self.get_option('keyvault_name') is not None:
        keyvault_name = self.get_option('keyvault_name')

      keyvault_uri = 'https://'+keyvault_name+'.vault.azure.net/'

      try:
        credentials = AzureCliCredential()

        secret_client = SecretClient(keyvault_uri, credentials)

      except Exception as err:
        raise AnsibleError(f"ERROR connecting to <{keyvault_uri}>: {err}")

      for term in terms:
          display.debug("azure_keyvault lookup term: %s" % term)

          try:
            secret = secret_client.get_secret(term)
          except Exception as err:
            raise AnsibleError(f"ERROR getting secret <{term}> from <{keyvault_uri}>: {err}")

          ret.append(secret.value)

          # consume an option: if this did something useful, you can retrieve the option value here

      return ret