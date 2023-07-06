#!/bin/bash

limit=$1

if [ -z "$limit" ]
then
    echo "ERROR: limit argument required"
    exit 13
fi

set -x
ansible-playbook server_top_role.yml --limit "$@"