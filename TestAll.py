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
        'cmd_tmpl': './webapps/test_http.bin -port=%(port)d -size=%(processes)d 2>/dev/null 1>/dev/null',
        'port' : 9001,
        'results': []
    },
    'test_martini.go': {
        'cmd_tmpl': './webapps/test_martini.bin -port=%(port)d -size=%(processes)d 2>/dev/null 1>/dev/null',
        'port': 9002,
        'results': []
    },
    'test_tornado.py': {
        'port': 8001,
        'cmd_tmpl': './webapps/test_tornado.py --port=%(port)d --processes=%(processes)d  2>/dev/null 1>/dev/null',
        'results': []
    },
    'test_webpy_gevent.py': {
        'port': 8002,
        # 'cmd_tmpl': 'gunicorn --certfile=cert.pem --keyfile=key.pem -k gevent -w %(processes)d -b 0.0.0.0:%(port)d test_webpy_gevent:wsgiapp 2>/dev/null 1>/dev/null',
        'cmd_tmpl': 'cd webapps && gunicorn -k gevent -w %(processes)d -b 0.0.0.0:%(port)d test_webpy_gevent:wsgiapp 2>/dev/null 1>/dev/null',
        'results': []
    },
    # 'test_webpy_gevent.py-UWSGI' : {
    #     'port': 8003,
    #     # 'cmd_tmpl': 'uwsgi --gevent 100 --gevent-monkey-patch -M --processes %(processes)d --https 0.0.0.0:%(port)d,cert.pem,key.pem --wsgi-file test_webpy_gevent.py --callable wsgiapp 2>/dev/null 1>/dev/null',
    #     'cmd_tmpl': 'cd webapps && uwsgi --gevent 100 --gevent-monkey-patch -M --processes %(processes)d --http 0.0.0.0:%(port)d --wsgi-file test_webpy_gevent.py --callable wsgiapp 2>/dev/null 1>/dev/null',
    #     'results': []
    # }
}

CONCURRENTS = [200, 400, 600, 800, 1000]
PROCESSES_LST = [1, 4, 8, 16, 32, 100, 200]
SECONDS = 15

REGEXPS = {
    'availability(%)' : r'^Availability.*\b(\d+\.\d+)\b.*',
    'transaction-rate(trans/sec)': r'^Transaction rate.*\b(\d+\.\d+)\b.*'
}


def kill_proc_tree(pid, including_parent=True):    
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):
        try:
            child.kill()
        except psutil.NoSuchProcess:
            pass
    if including_parent:
        try:
            parent.kill()
        except psutil.NoSuchProcess:
            pass

        
def time_now():
    return datetime.now().strftime("%m-%d_%H-%M-%S")


def ping(url):
    status = False
    req = None
    try:
        req = requests.get(url, verify=False, timeout=2)
    except Exception as e:
        print 'Ping failed:', url, e
        time.sleep(30)

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
            kill_proc_tree(p.pid)
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
        time.sleep(3)


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
    def cmp_res(a, b):
        c1, c2 = a['concurrent'], b['concurrent']
        if c1 > c2: return 1
        if c1 < c2: return -1
        
        p1, p2 = a['processes'], b['processes']
        if p1 > p2: return 1
        if p1 <= p2: return -1


    for k, info in SUMMARY.iteritems():
        cmd_tmpl = info['cmd_tmpl']
        port = info['port']
        ip = ETH0_IP
        test_url = 'http://%(ip)s:%(port)d/hello' % locals()
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
            
        results.sort(cmp=cmp_res)
        print '======================================================\n\n'
            
    with open(os.path.join('results', '{0}_summary.json'.format(time_now())), 'w') as f:
        f.write(json.dumps(SUMMARY, indent=4))


if __name__ == '__main__':
    main()
