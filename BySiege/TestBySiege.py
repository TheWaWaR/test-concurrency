#!/usr/bin/env python
#coding: utf-8

import os
import sys
import time
import json
from datetime import datetime

"""
   TODO:
   =====
     1. Bug fix: http://longmu.blog.51cto.com/431337/943009
"""

def time_fmt(t=None):
    if t is None:
        t = datetime.now()
    return t.strftime("%y-%m-%d_%H:%M:%S")


def backup():
    if os.path.exists('log'):
        if not os.path.exists('backups'):
            os.mkdir('backups')
        backup_dir = './backups/log_%s' % time_fmt()
        os.rename('log', backup_dir)
        print 'Backup to:', backup_dir
    os.mkdir('log')
    

def load_config(path):
    with open(path, 'r') as f:
        s = f.read()
        print s
        return json.loads(s)


def check_files(cfg):
    if 'POST' not in cfg['methods']:
        return
        
    post_file = cfg['methods']['POST']['post_file']
    if not os.path.exists(post_file):
        print 'JSON file(for POST) not exists: ', post_file
        sys.exit(-1)

def parse_result(logfile):
    result = {}
    with open(logfile) as f:
        for line in f.readlines():
            try:
                key, v = line.split(':')
                value = v.split()[0]
                try:
                    result[key] = float(value)
                except ValueError:
                    pass
            except ValueError: pass
    print 'Parsed: %s' % json.dumps(result, indent=4)
    return result


def parse_requests(logfile):
    requests = []
    with open(logfile) as f:
        for line in f.readlines():
            pos = line.find('HTTP/1.1')
            if pos > -1:
                status_code, cost = line.split()[1:3]
                status_code = int(status_code)
                cost = float(cost)
                requests.append((status_code, cost))
    print 'Parsed %s: <%d> records' % (logfile, len(requests))
    return requests


def mk_siege_cmd(cfg, method, concurrency):
    tag_tmpl = '%(method)s_%(test_time)s_%(concurrency)d'
    cmd_tmpl = 'siege -t %(test_time)s -c %(concurrency)d %(redirect_log)s %(headers)s %(url)s '
    header_tmpl = '-H "%s: %s"'
    url_post_tmpl = '"%s POST < %s"'
    urls_tmpl = '-f %s'
    log_tmpl = '1>%s 2>%s'

    info = cfg['methods'][method]
    test_time = cfg['test_time']
    headers = ' '.join([header_tmpl % (k, v) for k, v
                        in info['headers'].iteritems()])
    
    url = info.get('url', None)
    if url is None:
        # Means method==GET and use urls file
        url = urls_tmpl % info['urls_file']
    elif method == 'POST':
        post_file = info['post_file']
        url = url_post_tmpl % (url, post_file)
        
    tag = tag_tmpl % locals()
    requests_log = './log/requests_%s.log' % tag
    result_log = './log/result_%s.log' % tag
    redirect_log = log_tmpl % (requests_log, result_log)
    cmd = cmd_tmpl % locals()

    return cmd, requests_log, result_log


def start_tests():
    
    cfg = load_config('siege-config.json')
    backup()
    check_files(cfg)

    result_records = []
    for method in ('GET', 'POST'):
        for concurrency in cfg['concurrencies']:
            cmd, requests_log, result_log = mk_siege_cmd(cfg, method, concurrency)
            print '[CMD.%s]: %s' % (method, cmd)
            print '----------'
            t1 = datetime.now()
            os.system(cmd)
            t2 = datetime.now()
            record = {
                'method': method,
                'concurrency': concurrency,
                'time_start': time_fmt(t1),
                'time_end': time_fmt(t2),
                'result': parse_result(result_log),
                'requests': parse_requests(requests_log),
            }
            result_records.append(record)
            
            with open(result_log) as f:
                print f.read()
            print '----------------------------------------\n'
            time.sleep(cfg['test_interval'])
        print '============================================================\n\n'
        
    with open(cfg['summary_file'], 'w') as f:
        f.write(json.dumps(result_records))
    print '<<DONE>>'

if __name__ == '__main__':
    start_tests()
