#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# $File: sample_and_record.py
# $Date: Wed Mar 12 23:03:06 2014 +0800
# $Author: jiakai <jia.kai66@gmail.com>

from gevent import monkey
monkey.patch_all()

import gevent
import re
import json
import urllib2
import subprocess
import os
import os.path
import sqlite3
import calendar
import sys
from datetime import datetime

from dataproc import lowratio2concentration, aqi2concentration

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'history.db')
LOCAL_SAMPLE_EXE = os.path.join(os.path.dirname(__file__), 'getsample')

def get_conc_aqicn():
    """:return: tuple(<US data>, <Haidian data>)"""
    URL = 'http://aqicn.org/city/beijing'

    def parse_page(page):
        p0 = page.find('var localCityData =')
        p0 = page.find('{', p0)
        p1 = page.find(';', p0)
        p1 = page.rfind(']')
        data = page[p0:p1+1] + '}'
        return json.loads(data)

    page = urllib2.urlopen(URL).read()
    data = parse_page(page)['Beijing']
    rst = [-1, -1]
    for i in data:
        if 'US Embassy' in i['city']:
            assert rst[0] == -1
            rst[0] = int(i['aqi'])
        if 'Haidian Wanliu' in i['city']:
            assert rst[1] == -1
            rst[1] = int(i['aqi'])
    return map(aqi2concentration, rst)


def get_conc_bjair():
    """:return: tuple(<US data>, <CN data>)"""
    URL = 'http://www.beijing-air.com'
    page = urllib2.urlopen(URL).read().decode('utf-8')
    data = re.split( ur'PM2.5浓度:([0-9]*)', page, re.MULTILINE)
    return map(int, [data[3], data[1]])

get_conc = get_conc_bjair


def init_db(conn):
    c = conn.cursor()
    c.execute("""CREATE TABLE history
              (time INTEGER PRIMARY KEY,
              pm1_ratio REAL,
              pm25_ratio REAL,
              local_conc REAL,
              us_conc REAL,
              cn_conc REAL,
              err_msg TEXT)""")
    for col in 'local', 'us', 'cn':
        c.execute("""CREATE INDEX idx_{0}_conc ON history ({0}_conc)""".format(
            col))
    conn.commit()

def get_db_conn():
    exist = os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    if not exist:
        init_db(conn)
    conn.row_factory = sqlite3.Row
    return conn


def get_local_sample():
    """:return: list(pm1 ratio, pm25 ratio)"""
    subp = subprocess.Popen(LOCAL_SAMPLE_EXE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = subp.communicate()
    if subp.poll() is not None:
        if subp.returncode:
            raise RuntimeError(
                'failed to run local sampler: ret={}\n{}\n{}\n'.format(
                    subp.returncode, stdout, stderr))
    lines = stdout.split('\n')
    return map(float, lines[:2])


def insert_db_entry():
    time = calendar.timegm(datetime.utcnow().timetuple())
    pm1_ratio, pm25_ratio, local_conc, us_conc, cn_conc = [-1] * 5
    err_msg = None
    job = gevent.spawn(get_conc)
    try:
        pm1_ratio, pm25_ratio = get_local_sample()
        local_conc = lowratio2concentration(pm1_ratio - pm25_ratio)
    except Exception as exc:
        err_msg = 'failed to sample locally: {}'.format(exc)

    job.join()
    try:
        if job.successful():
            us_conc, cn_conc = job.value
        else:
            raise job.exception
    except Exception as exc:
        if err_msg is None:
            err_msg = ''
        err_msg = 'failed to retrieve AQI: {}'.format(exc)


    conn = get_db_conn()
    conn.cursor().execute(
        """INSERT INTO history VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (time, pm1_ratio, pm25_ratio, local_conc, us_conc, cn_conc, err_msg))
    conn.commit()


if __name__ == '__main__':
    if sys.argv[1:] == ['test']:
        print get_conc_aqicn()
        print get_conc_bjair()
    else:
        insert_db_entry()

