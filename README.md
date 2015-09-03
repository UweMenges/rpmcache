# Introducing rpmcache
*cache downloaded packages for other machines in your lan*

rpmcache is a caching proxy for rpm packages, to be used as proxy by
eg. dnf. It should also work for other (eg. deb) packages, the only
special files are metadata files (config option 'md_files', eg.
repomd.xml) that are fetched again after a configurable time (config
option 'md_keep', in minutes) to be able to get updates.

## Requirements

For running standalone uwsgi in a virtualenv with pip, these packages
are required:

```
# dnf install python-virtualenv python-pip gcc libcurl-devel
```

## Running standalone uwsgi

```
$ cd rpmcache
$ virtualenv .
$ . bin/activate
(rpmcache)$ pip install --upgrade -r requirements.txt
(rpmcache)$ uwsgi uwsgi.ini
```

## Client configuration

I put this in /etc/dnf/dnf.conf of every client:

```
[main]
proxy=http://rpmcache.my.lan:8090
deltarpm=0
```

I also have that on the server, but with http://localhost:8090. I disable
deltarpm because LAN speed is fast enough and outweighs deltarpm effort.

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

