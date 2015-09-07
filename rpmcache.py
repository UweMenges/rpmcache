#!/usr/bin/python
""" rpmcache - cache downloaded packages for other machines in your lan

rpmcache is a caching proxy for rpm packages, to be used as proxy by
eg. dnf. It should also work for other (eg. deb) packages, the only
special files are metadata files (config option 'md_files', eg.
repomd.xml) that are fetched again after a configurable time (config
option 'md_keep', in minutes) to be able to get updates.
"""

import os
import sys
import time
import uwsgi
import pycurl
# from StringIO import StringIO
# from cgi import parse_qs, escape
import mimetypes

# just for testing/debugging
# from pprint import pformat

CONFIG = {
    'cache_dir': '/var/cache/rpmcache',
    'log_level': 4,                 # 0 = silence, 4 = debug
    'use_color': True,              # colorized output for terminal
    'md_files': ['repomd.xml'],     # list of metadata files
    'md_keep': 360,         # how many minutes to cache metadata files
    }


def log(msg):
    """ Log message.

    Log format is '<level>: <message>'.
    Level is one of 'D'(ebug), 'I'(nfo), 'W'(arn), 'E'(rror)
    Message is only printed if CONFIG['log_level'] >= message level.
    Use ANSI color codes if CONFIG['use_color'] is True.
    """
    level = msg.split(':')[0]
    text = ':'.join(msg.split(':')[1:])
    num = {'D': 4, 'I': 3, 'W': 2, 'E': 1}
    color = {
        'D': '\033[01;30m', 'I': '\033[01;37m',
        'W': '\033[01;33m', 'E': '\033[01;31m',
        'off': '\033[00m'
        }
    if CONFIG['log_level'] >= num[level]:
        if CONFIG['use_color']:
            # print(color[level] + level + color['off'] + ':' + text)
            # print(color[level] + level + ':' + text + color['off'])
            sys.stdout.write(color[level] + level + ':' + text +
                             color['off'] + '\n')
            sys.stdout.flush()
        else:
            print(msg)
        return True
    else:
        return False

# example request from dnf upgrade
# GET ftp://ftp.informatik.uni-frankfurt.de/pub/Mirrors/fedora\
#       /updates/22/x86_64/repodata/repomd.xml


def localfile(url):
    """Return a local file path/name from given url."""
    dest = '/'.join(url.split('/')[2:])
    # TODO: sanitize dest (../../) to prevent writing outside cache_dir
    dest = '/'.join([CONFIG['cache_dir'], dest])
    return dest


def get_url(url):
    """Download a file from url to cache_dir."""
    # set a lock to prevent multiple simultaneous downloads of the same
    # file
    mypid = os.getpid()
    uwsgi.lock()
    otherpid = uwsgi.cache_get(url)
    if otherpid:
        uwsgi.unlock()
        while otherpid:
            log('D: pid %d waiting for pid %d to download %s' %
                (mypid, otherpid, url))
            time.sleep(1)
            otherpid = uwsgi.cache_get(url)
    else:
        uwsgi.cache_set(url, str(mypid))
        uwsgi.unlock()
        log('D: pid %d downloading %s' % (mypid, url))

    dest = localfile(url)
    if os.path.exists(dest):
        return 200

    curl = pycurl.Curl()
    curl.setopt(curl.URL, url)
    path = '/'.join(dest.split('/')[:-1])
    if not os.path.exists(path):
        # parallel download of rpms in subdir will create it right now
        try:
            os.makedirs(path)
        except OSError as e:
            # this catches duplicate creation (so just W not E)
            # TODO: need to bypass the open() on real errors
            # like permissions
            log('W: OS error(%d): %s' % (e.errno, e.strerror))
    with open(dest, 'wb') as fil:
        curl.setopt(curl.WRITEFUNCTION, fil.write)
        curl.perform()
    uwsgi.cache_del(url)
    return curl.getinfo(curl.HTTP_CODE)


def application(env, start_response):
    """Process request that is given via WSGI."""
    # log("D: env=%s" % pformat(env.items()))
    must_fetch = False
    url = env.get('REQUEST_URI')
    log("I: GET %s" % url)
    lfile = localfile(url)
    # metadata files must expire or we will never get updates again
    lfile_name = lfile.split('/')[-1]
    if lfile_name in CONFIG['md_files'] and os.path.exists(lfile):
        mtime = os.path.getmtime(lfile)
        now = float(time.strftime('%s'))
        delta = mtime + 60 * CONFIG['md_keep'] - now
        if delta < 0:
            must_fetch = True
        log('D: %s mtime=%s now=%s md_keep=%s delta=%s '
            'must_fetch=%s' %
            (lfile_name, mtime, float(now),
             60 * float(CONFIG['md_keep']), delta, must_fetch))

    if os.path.isdir(lfile):    # a little safeguard for browser
        start_response('422 Unprocessable Entry',
                       [('Content-Type', 'text/plain')])
        return ['Directory listing not supported.\n'
                'This is rpmcache, use a proxy= line '
                'in dnf.conf to use it.']

    if not os.path.exists(lfile) or must_fetch:
        log("W: fetching %s" % lfile)
        response = get_url(url)
        log("D: response=%s" % response)
        # TODO: handle response
    else:
        log("I: cache hit %s" % lfile)

    (mime_type, encoding) = mimetypes.guess_type('file://' + lfile)
    log("D: mime_type=%s encoding=%s" % (mime_type, encoding))
    size = os.path.getsize(lfile)
    log("D: size=%s" % size)
    start_response('200 OK', [
        ('Content-Type', str(mime_type)),
        ('Content-Length', str(size)),
        ('Content-Encoding', str(encoding)),
        ('Content-Disposition', 'attachment; filename=' +
         str(lfile_name))
    ])
    log("I: send file %s" % lfile)
    fil = open(lfile, 'rb')
    if 'wsgi.file_wrapper' in env:
        return env['wsgi.file_wrapper'](fil, 4096)
    else:
        return iter(lambda: fil.read(4096), '')

if __name__ == '__main__':
    def start_response(code, header):
        """ Define start_restponse when run as non-wsgi """
        print(code)
        print(header)

    print(application({'REQUEST_URI': '/'}, start_response))
