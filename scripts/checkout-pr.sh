#!/bin/sh

# Script credits to https://www.github.com/astorije

set -e

if [ -z "$1" ]; then
  echo "No pull request ID was specified."
  exit 1
fi

git fetch https://github.com/OpenPoGo/OpenPoGoBot.git refs/pull/${1}/head
git checkout FETCH_HEAD
