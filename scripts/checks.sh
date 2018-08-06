#!/usr/bin/env bash
set -e

default_command=( mypy flake8 )
for command in ${@:-"${default_command[@]}"}
do
    pre-commit run ${command} --all-files
done

python -m unittest