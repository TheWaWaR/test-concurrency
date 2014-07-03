#!/usr/bin/env python
#coding: utf-8

import os
import re
import json
import time
import subprocess
from datetime import datetime

import psutil
import requests


TEST_REQ_URL = 'http://192.168.40.215:8999/test'
ETH0_IP = '192.168.3.235'

SUMMARY = {
    'test_http.go': {
        'cmd_tmpl': './test_http.bin -port=%(port)d -size=%(processes)d 2>/dev/null 1>/dev/null',
        'port' : 9001,
        'results': []
    },
    'test_martini.go': {
        'cmd_tmpl': './test_martini.bin -port=%(port)d -size=%(processes)d 2>/dev/null 1>/dev/null',
        'port': 9002,
        'results': []
    },
    'test_tornado.py': {
        'port': 8001,
        'cmd_tmpl': 'python test_tornado.py --port=%(port)d --processes=%(processes)d  2>/dev/null 1>/dev/null',
        'results': []
    },
    'test_webpy_gevent.py': {
        'port': 8002,
        'cmd_tmpl': 'gunicorn --certfile=cert.pem --keyfile=key.pem -k gevent -w %(processes)d -b 0.0.0.0:%(port)d test_webpy_gevent:wsgiapp 2>/dev/null 1>/dev/null',
        'results': []
    },
    'test_webpy_gevent.py-UWSGI' : {
        'port': 8003,
        'cmd_tmpl': 'uwsgi --gevent 100 --gevent-monkey-patch -M --processes %(processes)d --https 0.0.0.0:%(port)d,cert.pem,key.pem --wsgi-file test_webpy_gevent.py --callable wsgiapp 2>/dev/null 1>/dev/null',
        'results': []
    }
}

CONCURRENTS = [200]#, 400, 600, 800, 1000]
PROCESSES_LST = [1]#, 4, 8, 16, 32, 100, 200]
SECONDS = 5

REGEXPS = {
    'availability' : r'^Availability.*\b(\d+\.\d+)\b.*',
    'rate': r'^Transaction rate.*\b(\d+\.\d+)\b.*'
}


def kill_proc_tree(pid, including_parent=True):    
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):
        child.kill()
    if including_parent:
        parent.kill()

        
def time_now():
    return datetime.now().strftime("%m-%d_%H-%M-%S")


def ping(url):
    status = False
    req = None
    try:
        req = requests.get(url, verify=False, timeout=2)
    except Exception as e:
        print 'Ping failed:', url, e

    if req and req.status_code == 200:
        status = True
    return status
    

def gen_server_results(cmd_tmpl, port, test_url):
    for processes in PROCESSES_LST:
        cmd = cmd_tmpl % locals()
        print 'Server:', cmd
        p = subprocess.Popen(cmd, shell=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        time.sleep(0.5)
        if not ping(test_url):
            yield {
                'processes': processes,
                'concurrent': -1,
                'output': 'PingError'
            }
            continue
            
        for concurrent in CONCURRENTS:
            data = do_test(test_url, concurrent, seconds=SECONDS)
            result = {
                'processes': processes,
                'concurrent': concurrent,
                'output': data['output']
            }
            yield result
            
        kill_proc_tree(p.pid)
        time.sleep(5)


HEADERS = {'Content-type': 'application/json', 'Accept': 'text/plain'}
def do_test(test_url, concurrent, seconds=20):
    data = {
        'url': test_url,
        'concurrent': concurrent,
        'seconds': seconds,
    }
    timeout = seconds + 10
    retry = 3
    while retry > 0:
        try:
            req = requests.post(TEST_REQ_URL, headers=HEADERS, data=json.dumps(data), timeout=timeout)
            return req.json()
        except requests.Timeout as e:
            print (3-retry), e
            retry -= 1


def main():
    for k, info in SUMMARY.iteritems():
        cmd_tmpl = info['cmd_tmpl']
        port = info['port']
        ip = ETH0_IP
        test_url = 'https://%(ip)s:%(port)d/hello' % locals()
        results = info['results']
        print 'Section:', k, test_url
        print time_now()
        print '=================='
        
        for result in gen_server_results(cmd_tmpl, port, test_url):
            print 'section: {0}, processes: {1}, concurrent: {2}'.format(k, result['processes'], result['concurrent'])
            output = result.pop('output')
            for line in output.split('\n'):
                for name, regexp in REGEXPS.iteritems():
                    m = re.match(regexp, line)
                    if m:
                        match_result = m.groups()[0]
                        result[name] = float(match_result)
                        break

            print '--------------------'
            print output
            print '--------------------'
            print time_now()
            print '----------------------------------------\n'
            results.append(result)
        print '======================================================\n\n'
            
    with open(os.path.join('results', '{0}_summary.json'.format(time_now())), 'w') as f:
        f.write(json.dumps(SUMMARY, indent=4))


if __name__ == '__main__':
    main()
