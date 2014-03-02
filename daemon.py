#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# $File: daemon.py
# $Date: Sun Mar 02 20:25:35 2014 +0800
# $Author: jiakai <jia.kai66@gmail.com>

from sample_and_record import insert_db_entry

import time

SAMPLE_DELTA = 300

if __name__ == '__main__':
    while True:
        insert_db_entry()
        time.sleep(SAMPLE_DELTA)

