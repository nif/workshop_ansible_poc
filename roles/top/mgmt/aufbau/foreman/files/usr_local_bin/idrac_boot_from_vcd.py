#!/usr/bin/env python3

import os
import sys
import inspect
import yaml
import argparse
import paramiko
import stat

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
python_lib_dir = os.path.join(parent_dir, 'python_lib')
sys.path.insert(0, python_lib_dir) 

from dvag_functions import struct_to_yaml

IDRAC_CONFIG_FILE = '~/.idrac_conf.yaml'

def read_idrac_config():
    idrac_config_file = os.path.expanduser(IDRAC_CONFIG_FILE)

    if not os.path.exists(idrac_config_file):
        print(f"ERROR!!: file {idrac_config_file} does not exist")
        os.exit(13)

    st = os.stat(idrac_config_file)
    if bool(st.st_mode & stat.S_IRGRP) or bool(st.st_mode & stat.S_IRWXO):
        print(f'ERROR!!: bad file permissions  "{idrac_config_file}" - can only be  readable for owner')
        os.exit(23)

    with open(idrac_config_file, 'r') as cf_o:
        config_data = yaml.safe_load(cf_o)

    idrac_user = config_data.get('idrac_user')
    if idrac_user is None:
        print(f'ERROR!!: idrac_user not defined')
        os.exit(33)

    idrac_password = config_data.get('idrac_password')
    if idrac_password is None:
        print(f'ERROR!!: idrac_password not defined')
        os.exit(43)

    return idrac_user, idrac_password

parser = argparse.ArgumentParser(description='run idrac commands via ssh')
parser.add_argument('--idrac_ip', help='idrac ip', required=True)
parser.add_argument('--mac', help='mac of interface to check', required=True)
parser.add_argument('--nic_num', help='racadm nic_num of interface to check mac', required=False)
args = parser.parse_args()

idrac_user = os.environ.get('IDRAC_USER')
idrac_password = os.environ.get('IDRAC_PASSWORD')

if idrac_password is None:
    idrac_user, idrac_password = read_idrac_config()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    args.idrac_ip,
    username=idrac_user,
    password=idrac_password
)

def racadm_cmd(cmd=None):

    if cmd is None:
        raise Exception("ERROR!!!: cmd arg is required")

    stdin, stdout, stderr = client.exec_command(cmd)
    stdin.close()

    stdout_str = stdout.read().decode('utf-8')
    stderr_str = stderr.read().decode('utf-8')
    rc = stdout.channel.recv_exit_status()

    ret = {
        'cmd': cmd,
        'out': stdout_str,
        'err': stderr_str,
        'rc': rc
    }

    return ret

nic_num = 1
if args.nic_num is not None:
    nic_num = args.nic_num

cmd = f"racadm get NIC.VndrConfigPage.{nic_num}.MacAddr"

ret = racadm_cmd(cmd=cmd)

out_lower = ret['out'].lower()
mac_lower = args.mac.lower()

if out_lower.find(mac_lower) == -1:
    raise Exception(f"ERROR!!!: mac={mac_lower} was not found in racadm out={out_lower} ret={ret}")

print(struct_to_yaml(ret))

ret = racadm_cmd('racadm set idrac.serverboot.FirstBootDevice VCD-DVD')
out_lower = ret['out'].lower()
if out_lower.find('success') == -1:
    raise Exception(f'ERROR!!!: "success" was not found in racadm out={out_lower} ret={ret}')
print(struct_to_yaml(ret))

ret = racadm_cmd('racadm set idrac.serverboot.BootOnce Enabled')
out_lower = ret['out'].lower()
if out_lower.find('success') == -1:
    raise Exception(f'ERROR!!!: "success" was not found in racadm out={out_lower} ret={ret}')
print(struct_to_yaml(ret))

ret = racadm_cmd('racadm serveraction powercycle')
out_lower = ret['out'].lower()
if out_lower.find('success') == -1:
    raise Exception(f'ERROR!!!: "success" was not found in racadm out={out_lower} ret={ret}')
print(struct_to_yaml(ret))
