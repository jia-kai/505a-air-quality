#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# $File: daemon.py
# $Date: Mon Mar 03 09:35:26 2014 +0800
# $Author: jiakai <jia.kai66@gmail.com>

from sample_and_record import insert_db_entry

import time

MIN_UPTIME = 120
SAMPLE_DELTA = 300

def get_uptime():
    with open('/proc/uptime') as fin:
        return map(float, fin.read().split())[0]

if __name__ == '__main__':
    if get_uptime() < MIN_UPTIME:
        time.sleep(MIN_UPTIME)
    while True:
        insert_db_entry()
        time.sleep(SAMPLE_DELTA)

