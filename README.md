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
# dnf install python3-virtualenv python-pip gcc libcurl-devel
```

## Running standalone uwsgi

```
$ cd rpmcache
$ virtualenv .
$ . bin/activate
(rpmcache)$ pip install --upgrade -r requirements.txt
(rpmcache)$ uwsgi uwsgi.ini
```

## Running uwsgi with systemd

See also http://uwsgi-docs.readthedocs.io/en/latest/Systemd.html, but I
prefer to run it directly.

Create user for rpmcache, make cache dir, switch user, clone repo,
create virtualenv and install:
```
# useradd -c 'rpmcache user' -m -r -s /sbin/nologin rpmcache 
# install -d -m 775 -g rpmcache -o rpmcache /var/cache/rpmcache
# su rpmcache -s /bin/bash -l
$ git clone https://github.com/UweMenges/rpmcache.git
$ cd rpmcache
$ virtualenv .
$ . bin/activate
(rpmcache)$ export PYCURL_SSL_LIBRARY=openssl
(rpmcache)$ pip install --upgrade -r requirements.txt
(rpmcache)$ exit
```

Install and enable the systemd unit file:
```
# cp rpmcache.service /etc/systemd/system/
# systemctl enable rpmcache
```

### SELinux

Create and install the policy file:
```
# checkmodule -M -m -o rpmcache.mod rpmcache.te
# semodule_package -o rpmcache.pp -m rpmcache.mod
# semodule -X 300 -i rpmcache.pp
```

Start rpmcache: `systemctl start rpmcache`


## Client configuration

I put this in /etc/dnf/dnf.conf of every client:

```
[main]
proxy=http://rpmcache.my.lan:8090
deltarpm=0
```

I also have that on the server, but with http://localhost:8090. I disable
deltarpm because LAN speed is fast enough and outweighs deltarpm effort.

As rpmcache only works for unencrypted requests, the `.repo` files need
to be adjusted. For lazyness, this can be done with `sed` on the default
Fedora `.repo` files:

```
# cd /etc/yum.repos.d/
# sed -i 's/^metalink/#&/g; s/^#baseurl/baseurl/g' *.repo
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

