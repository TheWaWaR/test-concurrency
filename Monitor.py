#!/usr/bin/env python
#coding: utf-8


import os
import sys
import time
import commands
import json
from datetime import datetime
from threading import Thread
import subprocess


UPTIME_INTERVAL = 5
MEM_INTERVAL = 5
CPU_USAGE_INTERVAL = 5
RUNNING = True

MEM_FILE = 'mem.log'
UPTIME_FILE = 'uptime.log'
CPU_USAGE_FILE = 'cpu_usage.log'

def log_uptime(interval, logfile):
    global RUNNING
    print 'Start uptime'
    f = open(logfile, 'w')
    while RUNNING:
        output = commands.getoutput('uptime')
        # print output
        f.write(output + "\n")
        f.flush()
        time.sleep(interval)
    f.close()
    print 'UPTIME END'


def log_mem(interval, logfile):
    global RUNNING
    print 'Start mem'
    f = open(logfile, 'w')
    while RUNNING:
        output = commands.getoutput('free -m')
        # print output
        f.write(str(datetime.now()) + '\n')
        f.write(output + '\n')
        f.flush()
        time.sleep(interval)
    f.close()
    print 'MEM END'


cpu_usage_p = None
def cpu_usage(interval, logfile):
    global cpu_usage_p
    cmd = 'iostat -ct %d >%s' % (interval, logfile)
    print cmd
    cpu_usage_p = subprocess.Popen(cmd, shell=True)
    cpu_usage_p.wait()
    print 'CPU USAGE END'
    

def start():
    uptime_t = Thread(target=log_uptime, args=(UPTIME_INTERVAL, UPTIME_FILE))
    uptime_t.start()
    
    mem_t = Thread(target=log_mem, args=(MEM_INTERVAL, MEM_FILE))
    mem_t.start()

    cpu_t = Thread(target=cpu_usage, args=(CPU_USAGE_INTERVAL, CPU_USAGE_FILE))
    cpu_t.start()

    try:
        cpu_t.join()
        uptime_t.join()
    except KeyboardInterrupt:
        global RUNNING, cpu_usage_p
        RUNNING = False
        print cpu_usage_p.pid
        try:
            cpu_usage_p.kill()
        except OSError as e:
            print e
        cpu_t.join()
        uptime_t.join()
        mem_t.join()

if __name__ == '__main__':
    start()
