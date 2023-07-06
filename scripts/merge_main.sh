#!/bin/bash

branch=$1

if [ -z "$branch" ]
then
    echo "ERROR: branch argument required"
    exit 13
fi

set -x
set -e

git checkout $branch
git merge main
git push
git checkout main