#!/usr/bin/env python3

import os
import sys
import inspect
import argparse
from datetime import datetime
import re
import pathlib

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
python_lib_dir = os.path.join(parent_dir, 'playbooks/module_utils')
sys.path.insert(0, python_lib_dir) 
python_lib_dir = os.path.join(parent_dir, 'python_lib')
sys.path.insert(0, python_lib_dir) 

from dvag_foreman_api import ForemanAPI
from dvag_functions import struct_to_yaml


parser = argparse.ArgumentParser(description='FOREMAN API http get')
parser.add_argument('--server', help='foreman server', required=False)
parser.add_argument('--host', help='host name', required=False)
parser.add_argument('--path', help='path to write inventory', required=True)

args = parser.parse_args()

inventory_dir = pathlib.Path(args.path)

now = datetime.now()

server = 'foreman01.1.mgmt.dvag.net'
if args.server is not None:
    server = args.server

foreman = ForemanAPI(verbose=False, server=server)

ans = foreman.get(url = 'hosts', search = args.host)
#print( struct_to_yaml(ans) )
#sys.exit(0)

results = ans['data']['results']

for result in results:

    host_data = {
        'timestamp_epoch': int(now.timestamp()),
        'timestamp_str': now.strftime('%Y-%m-%d %H:%M:%S')
    }

    interesting_keys = [
        'architecture_name',
        'creator',
        'domain_name',
        'environment_name',
        'errata_status_label',
        'global_status_label',
        'hostgroup_title',
        'ip',
        'location_name',
        'model_name',
        'name',
        'operatingsystem_name',
        'organization_name',
        'owner_name',
        'subnet_name',
    ]

    if result.get('model_name') is not None:
        if re.search('vmware', result['model_name'], re.IGNORECASE) is not None:
            interesting_keys += [
                'compute_profile_name',
                'compute_resource_name',
                'compute_resource_provider'
            ]

    for key in interesting_keys:
        if result.get(key) is not None:
            host_data[key] = result[key]
        else:
            host_data[key] = None

    fqdn = host_data['name']

    filepath = inventory_dir / f"{fqdn}.yaml"
    with filepath.open("w", encoding ="utf-8") as f:
        f.write("---\n\n")
        f.write( struct_to_yaml(host_data) )

