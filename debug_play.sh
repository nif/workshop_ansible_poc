#!/bin/bash

host=$1

if [ -z "$host" ]
then
    echo "ERROR: host argument required"
    exit 13
fi

top_role=$(ansible-inventory --host $host | perl -lne '/top_role":\s"(.*)"/ && print $1')

#echo ">>>>$top_role<<<<"

if [ -z "$top_role" ]
then
    echo "ERROR: couldn't get top_role for host=$host"
    exit 18
fi

set -x
ansible-playbook server_top_role_static.yml --extra-vars static_role=$top_role --limit "$@"
