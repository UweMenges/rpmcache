#!/bin/bash
# dnf repomanag can't handle rpm in subdirs properly, so we need to call
# it separately for every dir containing .rpm files
for dir in $(find . -type f -name \*.rpm -exec dirname {} + | sort -u); do
    rpmfile=($(dnf repomanage -o "$dir"))
    [ -n "${rpmfile[0]}" ] && rm -v ${rpmfile[@]}
done

for dir in $(find . -type d -name repodata); do
    [ ! -e "$dir/repomd.xml" ] && continue
    cd "$dir" && { for file in *.gz *.xz; do
	if grep "$file" repomd.xml; then
	    echo "keep $file"
	else
	    rm "$file" 2> /dev/null
	fi
    done; cd -; }
done
