#!/usr/bin/env python
#coding: utf-8

import os
import sys
import time
import json
from datetime import datetime

def time_fmt(t=None):
    if t is None:
        t = datetime.now()
    return t.strftime("%y-%m-%d_%H:%M:%S")

if os.path.exists('log'):
    if not os.path.exists('backups'):
        os.mkdir('backups')
    backup_dir = './backups/log_%s' % time_fmt()
    os.rename('log', backup_dir)
    print 'Backup to:', backup_dir
    
os.mkdir('log')


HOST = '10.162.207.221'
PORT = 8080
JSON_FILE = './post_new.json'
SUMMARY_FILE = './log/summary.json'
SLEEP_SECONDS = 0

CMD_TMPLS = {
    'GET': '''siege -t %(time)s -c %(concurrency)d \
  -H "X-Client-ID: some-id" \
  -H "X-File-Name: some.mp4" \
  -H "X-File-Size: 12354" \
  -H "X-URL: thunder://QUFlZDJrOi8vfGZpbGV8JUU2JTlEJTgzJUU1JThBJTlCJUU3JTlBJTg0JUU2JUI4JUI4JUU2JTg4JThGLkdhbWUub2YuVGhyb25lcy5TMDRFMTAuRW5kLiVFNCVCOCVBRCVFOCU4QiVCMSVFNSVBRCU5NyVFNSVCOSU5NS5IRFRWcmlwLjYyNFgzNTIubXA0fDMxOTcxNzEwNXwxMjJhZmZiZTExYjFiNjkzOGQ1MWUwNzMxNjc3NTRhMnxoPWhjNmZibm9oZm9hdXgzc2trcXh5emp4dXNvaDVhdXR3fC9aWg==" \
  "http://%(host)s:%(port)d/copyrighted?key=this-is-TMP-apikey&digest-algorithm=sha1&digest=953109996fc9a5841b44ab4e37b12b83025b9eb3" \
  1>%(req_log)s 2>%(result_log)s''',
    
    'POST': 'siege -t %(time)s -c %(concurrency)d \
  -H "Content-Type:application/json" \
  -H "X-Client-ID: client_id123456" \
  -H "X-Mime-Type: video/mp4" \
  "http://%(host)s:%(port)d/copyrighted?key=this-is-TMP-apikey&hash=test&digest=0580bd7f4abc33f5353fc37a2919049eec2c7c6d&digest-algorithm=sha1 POST < %(json_file)s" \
   1>%(req_log)s 2>%(result_log)s'
}

# req_time = '10s'
# concurrencies = [100, 200]
req_time = '5m'
concurrencies = [300, 600, 900, 1200, 1500]

RESULT_RECORDS = []

if not os.path.exists(JSON_FILE):
    print 'JSON file(for POST) not exists: ', JSON_FILE
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


def start_tests():
    
    for method in ('GET', 'POST'):
        for c in concurrencies:
            tag = '%s_%s_%d'  % (method, req_time, c)
            req_log = './log/req_%s.log' % tag
            result_log = './log/result_%s.log' % tag
            args = {
                'host': HOST,
                'port': PORT,
                'time': req_time,
                'concurrency': c,
                'req_log': req_log,
                'result_log': result_log,
            }
            if method == 'POST':
                args['json_file'] = JSON_FILE
                
            cmd = CMD_TMPLS[method] % args
            print '[CMD.%s]: %s' % (method, cmd)
            print '----------'
            t1 = datetime.now()
            os.system(cmd)
            t2 = datetime.now()
            record = {
                'args': args,
                'time_start': time_fmt(t1),
                'time_end': time_fmt(t2),
                'result': parse_result(result_log),
                'requests': parse_requests(req_log),
            }
            RESULT_RECORDS.append(record)
            
            with open(result_log) as f:
                print f.read()
            print '----------------------------------------\n'
            time.sleep(SLEEP_SECONDS)
        print '============================================================\n\n'
        
    with open(SUMMARY_FILE, 'w') as f:
        f.write(json.dumps(RESULT_RECORDS))
    print '<<DONE>>'

if __name__ == '__main__':
    start_tests()
