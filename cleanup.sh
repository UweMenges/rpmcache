#!/bin/bash
# TODO: implement cleanup in rpmcache.py

# dnf repomanage can't handle rpm in subdirs properly, so we need to call
# it separately for every dir containing .rpm files
for dir in $(find . -type f -name \*.rpm -exec dirname {} + | sort -u); do
    rpmfile=($(dnf repomanage -o "$dir"))
    [ -n "${rpmfile[0]}" ] && rm -v "${rpmfile[@]}"
done

shopt -s nullglob
for dir in $(find . -type d -name repodata); do
    [ ! -e "$dir/repomd.xml" ] && continue
    cd "$dir" && { for file in *.gz *.xz; do
	if grep "$file" repomd.xml >/dev/null; then
	    echo "keep $file"
	else
	    rm -v "$file"
	fi
    done; cd - >/dev/null; }
done

# remove 404 html files we got from old metadata queries
files=$(find /var/cache/rpmcache/ -type f -size -2k -exec file {} + \
    | grep HTML \
    | while read file rest; do
	echo ${file%:}
      done)
[ -n "$files" ] && rm -v "$files"
