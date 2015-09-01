#!/usr/bin/python
# rpm-cache - a caching proxy for dnf

import os
import sys
import time
import pycurl
#from StringIO import StringIO
#from cgi import parse_qs, escape
import mimetypes

# just for testing/debugging
#from pprint import pformat

config = {
    'cache_dir': '/var/cache/rpm-cache',
    'log_level': 4,         # 0 = silence, 4 = debug
    'use_color': True,      # colorized output for terminal
    'repomd_keep': 1440,    # how many minutes to cache repomd.xml
    }

# log format is <level>: <message>
# level is one of D(ebug) I(nfo) W(arn) E(rror)
def log(msg):
    level = msg.split(':')[0]
    text = ':'.join(msg.split(':')[1:])
    num = {'D': 4, 'I': 3, 'W': 2, 'E': 1}
    color = { 'D': '\033[01;30m', 'I': '\033[01;37m',
	'W': '\033[01;33m', 'E': '\033[01;31m', 'off': '\033[00m' }
    if config['log_level'] >= num[level]:
	if config['use_color']:
	    #print(color[level] + level + color['off'] + ':' + text)
#	    print(color[level] + level + ':' + text + color['off'])
	    sys.stdout.write(color[level] + level + ':' + text +
		    color['off'] + '\n')
	    sys.stdout.flush()
	else:
	    print(msg)
	return True
    else:
	return False
    
# example request from dnf upgrade
# GET ftp://ftp.informatik.uni-frankfurt.de/pub/Mirrors/fedora/updates/22/x86_64/repodata/repomd.xml

# make a local file path/name from url
def localfile(url):
    dest = '/'.join(url.split('/')[2:])
    # TODO: sanitize dest (../../) to prevent writing outside cache_dir
    dest = '/'.join([config['cache_dir'], dest])
    return dest

# download a file from url to cache_dir
def get_url(url):
    # TODO: set a lock to prevent multiple simultaneous downloads
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    dest = localfile(url)
    path = '/'.join(dest.split('/')[:-1])
    if not os.path.exists(path):
        os.makedirs(path)
    with open(dest, 'wb') as f:
	c.setopt(c.WRITEFUNCTION, f.write)
	c.perform()
    return c.getinfo(c.HTTP_CODE)

def application(env, start_response):
#    log("D: env=%s" % pformat(env.items()))
    must_fetch = False
    url = env.get('REQUEST_URI')
    log("I: GET %s" % url)
    lfile=localfile(url)
    # TODO: repomd.xml should expire or we will never get updates again
    lfile_name = lfile.split('/')[-1]
    if lfile_name == 'repomd.xml':
	mtime = os.path.getmtime(lfile)
	now = float(time.strftime('%s'))
	delta = mtime + 60 * config['repomd_keep'] - now 
	if delta < 0:
	    must_fetch = True
	log('D: %s mtime=%s now=%s repomd_keep=%s delta=%s must_fetch=%s' %
		(lfile_name, mtime, float(now),
		60 * float(config['repomd_keep']), delta, must_fetch))

    if os.path.isdir(lfile): # a little safeguard for browser
	start_response('422 Unprocessable Entry', [('Content-Type',
		    'text/plain')])
	return ['Directory listing not supported.\n'
	    'This is rpm-cache, use a proxy= line '
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
	    ('Content-Type', mime_type),
	    ('Content-Length', str(size)),
	    ('Content-Encoding', str(encoding)),
	    ('Content-Disposition',
		'attachment; filename=' + lfile_name)
	    ])
    log("I: send file %s" % lfile)
    f = file(lfile, 'rb')
    if 'wsgi.file_wrapper' in env:
	return env['wsgi.file_wrapper'](f, 4096)
    else:
	return iter(lambda: f.read(4096), '')

if __name__ == '__main__':
    def start_response(code, header):
	print(code)
	print(header)

    print(application({'REQUEST_URI': '/'}, start_response))
