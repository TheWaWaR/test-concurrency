#!/usr/bin/env python
#coding: utf-8

from gevent import monkey
monkey.patch_all()

import uuid
import sys
import gevent
from gevent.pool import Pool
from multiprocessing import Process
import requests
from datetime import datetime

TEST_URL = 'http://192.168.3.235:8081/copyrighted'
CONCURRENCY = int(sys.argv[1])
SECONDS = int(sys.argv[2])

COUNT = 0
TIMEOUT_CNT = 0

def test_get():
    headers = {
        'X-Progress': '20%',
        'X-Client-ID': '[client-id]',
        'X-Client-Address': '[client-address]',
        'X-File-Name': '[file-name]',
        'X-File-Size': '12345',
        'X-Mime-Type': 'audio/mp4',
        'X-URL': 'http://115.29.36.65/clips/youku_33.flv'
    }
    params = {
        'key': 'this-is-TMP-apikey',
        'hash': uuid.uuid1(),
        'digest': uuid.uuid1(),
        'digest-algorithm': 'sha1'
    }

    try:
        t1 = datetime.now()
        resp = requests.get(TEST_URL, headers=headers, params=params)
        global COUNT
        t2 = datetime.now()
        print datetime.now(), (t2-t1).seconds, resp.status_code, resp.text
        COUNT += 1
    except requests.Timeout as e:
        global TIMEOUT_CNT
        TIMEOUT_CNT += 1
        print '<timeout>'


def start_pool(size):
    t1 = datetime.now()
    pool = Pool(size)
    while (datetime.now() - t1).seconds <= SECONDS:
        print 'pool.free_count():', pool.free_count()
        if pool.free_count() == 0:
            pool.wait_available()
            print '<free 1>'
        pool.apply_async(test_get)
    print 'Joining............................................'
    pool.join()
    t2 = datetime.now()
    print COUNT, TIMEOUT_CNT
    print COUNT / (t2-t1).seconds


if __name__ == '__main__':
    processes = []
    for i in range(1):
        p = Process(target=start_pool, args=(CONCURRENCY,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
