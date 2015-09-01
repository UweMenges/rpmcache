# Introducing rpmcache

rpmcache is a caching proxy for rpm packages, to be used as proxy by
eg. dnf. It should also work for other (eg. deb) packages, the only
special files are metadata files (config option 'md_files', ege.
repomd.xml) that are fetched again after a configurable time (config
option 'md_keep', in minutes) to be able to get updates.

## Requirements

For running standalone uwsgi in a virtualenv with pip, these packages
are required:

```
# dnf install python-virtualenv python-pip gcc libcurl-devel uwsgi
```

## Running standalone uwsgi

```
$ cd rpmcache
$ virtualenv .
$ . bin/activate
(rpmcache)$ pip install --upgrade -r requirements.txt
(rpmcache)$ uwsgi uwsgi.ini
```

## Troubleshooting

On running uwsgi, there can be the error

```
ImportError: pycurl: libcurl link-time ssl backend (nss) is different from compile-time ssl backend (none/other)
```

It can be fixed by these steps:

```
(rpmcache)$ pip uninstall pycurl
(rpmcache)$ export PYCURL_SSL_LIBRARY=nss
(rpmcache)$ pip install pycurl
```

