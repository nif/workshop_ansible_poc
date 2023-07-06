import os
import sys
import inspect
import urllib3
import stat
import yaml
import requests
import getpass

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir) 
from dvag_functions import struct_to_yaml

FOREMAN_CONFIG_FILE = '~/.foreman_conf.yaml'

def read_foreman_config(foreman_config_file=FOREMAN_CONFIG_FILE, server=None):
    foreman_config_file = os.path.expanduser(foreman_config_file)

    ret = {
        'data': {},
        'error': None
    }

    if not os.path.exists(foreman_config_file):
        ret['error'] = f"file {foreman_config_file} does not exist"
        return ret

    st = os.stat(foreman_config_file)
    if bool(st.st_mode & stat.S_IRGRP) or bool(st.st_mode & stat.S_IRWXO):
        ret['error'] = f'bad file permissions  "{foreman_config_file}" - can only be  readable for owner'
        return ret

    with open(foreman_config_file, 'r') as cf_o:
        config_data = yaml.safe_load(cf_o)

    if server is None:
        ret['data'] = config_data
    else:
        if server in config_data:
            ret['data'] = config_data[server]
        else:
            ret['data'] = config_data

    return ret

class ForemanAPI():

    http_headers = {
        'content-type': 'application/json',
        'accept': 'application/json',
        'charset': 'utf-8',
    }

    http_params = { 
        'per_page': 2000,
        #'thin': 'true',
    }
 
    def get(self, url = None, search = None, params = None):
        if url is None:
            sys.exit(f'url must be defined')

        if self.verbose:
            print(f'HTTP_GET: url: "{url}" search: "{search}" params: "{params}"')

        http_params = self.http_params.copy()

        if search is not None:
            http_params['search'] = search

        if params is not None:
            http_params.update(params)

        try:
            r = self.session.get(
                url = self.api_base + url,
                headers = self.http_headers,
                params = http_params,
            )
        except Exception as e:
            sys.exit(e)

        if r.status_code == 200:
            error = ''
            data = r.json()
        else:
            if not self.katello:
                #error = r.json()['message']
                error = r.text
                data = None
            else:
                error = r.json()['displayMessage']
                data = None

        ans = {
            'status_code': r.status_code,
            'data': data,
            'error': error
        }
        return ans

    def post(self, url = None, json = None):
        if url is None:
            sys.exit(f'url must be defined')

        if json is None:
            sys.exit(f'json must be defined')

        if self.verbose:
            print(f'HTTP_POST: url: "{url}" json: "{json}"')

        params = self.http_params.copy()

        try:
            r = self.session.post(
                url = self.api_base + url,
                headers = self.http_headers,
                params = params,
                json = json,
            )
        except Exception as e:
            sys.exit(e)

        ans = {
            'status_code': r.status_code,
            'data': r.json(),
        }

        return ans

    def put(self, url = None, json = None):
        if url is None:
            sys.exit(f'url must be defined')

        if json is None:
            sys.exit(f'json must be defined')

        if self.verbose:
            print(f'HTTP_PUT: url: "{url}" json: "{json}"')

        params = self.http_params.copy()

        try:
            r = self.session.put(
                url = self.api_base + url,
                headers = self.http_headers,
                params = params,
                json = json,
            )
        except Exception as e:
            sys.exit(e)

        if r.status_code == 200:
            error = ''
            data = r.json()
        else:
            if not self.katello:
                #error = r.json()['message']
                error = r.text
                data = None
            else:
                error = r.json()['displayMessage']
                data = None

        ans = {
            'status_code': r.status_code,
            'data': data,
            'error': error
        }
        return ans

    def delete(self, url = None):
        if url is None:
            sys.exit(f'url must be defined')

        if self.verbose:
            print(f'HTTP_DELETE: url: "{url}"')

        params = self.http_params.copy()

        try:
            r = self.session.delete(
                url = self.api_base + url,
                headers = self.http_headers,
                params = params,
            )
        except Exception as e:
            sys.exit(e)

        data = r.json()

        ans = {
            'status_code': r.status_code,
            'data': data,
        }
        return ans

    def get_id(self, url = None, search = None):
        ans = self.get(url=url, search=search)
        #sys.exit(f'{struct_to_yaml(data)}')
        print(f'Get id for "{url}"?"{search}"')

        if ans['status_code'] != 200:
            sys.exit(f"ERR!! finding id with url={url} and search={search}\n{struct_to_yaml(ans)}")

        data = ans['data']

        if data['subtotal'] != 1:
            sys.exit(f"ERR!! subtotal!=1\n{struct_to_yaml(data)}")

        results = data['results']

        # required for puppetclasses
        if isinstance(results, dict) and 'roles' in results:
            results = results['roles']

        return results[0]['id']

    def __init__(self, 
            verbose=False,
            server=None,
            user=None,
            password=None,
            validate_certs=None,
            katello=False,
        ):

        self.verbose = verbose
        self.katello = katello
        self.server = server
        self.user = user
        self.password = password
        self.validate_certs = validate_certs

        if self.server is None:
            self.server = os.environ.get('FOREMAN_SERVER')

        if self.server is None:
            self.server = 'sheriff.1.mgmt.dvag.net'

        self.server_url = f"https://{self.server}"

        if self.user is None:
            self.user = os.environ.get('FOREMAN_USER')

        if self.password is None:
            self.password = os.environ.get('FOREMAN_PASSWORD')

        def to_bool(x):
            return not (x.lower() in ("false", "no","0") )

        if self.validate_certs is None:
            self.validate_certs = os.environ.get('FOREMAN_VALIDATE_CERTS')

            if self.validate_certs is not None:
                self.validate_certs = to_bool(foreman_validate_certs_from_env)

        foreman_config = read_foreman_config(server = server)
        config_error = foreman_config['error']
        config_data = foreman_config['data']

        if foreman_config['error'] is  None:
            # use config values if not defined

            if self.validate_certs is None:
                if config_data.get('foreman_validate_certs') is not None:
                    self.validate_certs = config_data.get('foreman_validate_certs')

            if self.user is None:
                if config_data.get('foreman_user') is not None:
                    self.user = config_data.get('foreman_user')

            if self.password is None:
                if config_data.get('foreman_password') is not None:
                    self.password = config_data.get('foreman_password')

        if self.validate_certs is None:
            self.validate_certs = False

        if self.user is None or self.password is None:
            if self.user is None:
                print('ERR!: foreman_user is not defined')
            if self.password is None:
                print('ERR!: foreman_password is not defined')
            if config_error is not None:
                print(f"ERR!: {config_error}")
            sys.exit(133)

        if self.katello:
            self.api_base = self.server_url + '/katello/api/'
        else:
            self.api_base = self.server_url + '/api/'

        self.session = requests.Session()
        self.session.auth = (self.user, self.password)

        if not self.validate_certs:
            self.session.verify = False
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
