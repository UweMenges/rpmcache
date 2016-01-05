#!/bin/bash
# dnf repomanag can't handle rpm in subdirs properly, so we need to call
# it separately for every dir containing .rpm files
for dir in $(find . -name \*.rpm -exec dirname {} + | sort -u); do
    rpmfile=($(dnf repomanage -o "$dir"))
    [ -n "${rpmfile[0]}" ] && rm -v ${rpmfile[@]}
done
