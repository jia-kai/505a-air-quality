#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# $File: sample_and_record.py
# $Date: Sun Mar 02 15:52:01 2014 +0800
# $Author: jiakai <jia.kai66@gmail.com>

from gevent import monkey
monkey.patch_all()

import gevent
import json
import urllib2
import subprocess
import os
import os.path
import sqlite3
import calendar
from datetime import datetime

from dataproc import lowratio2aqi

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'history.db')
LOCAL_SAMPLE_EXE = os.path.join(os.path.dirname(__file__), 'getsample')

assert os.path.isfile(LOCAL_SAMPLE_EXE)

def get_aqi():
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
    return rst


def get_db_conn():
    if os.path.exists(DB_PATH):
        return sqlite3.connect(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE history
              (time INTEGER PRIMARY KEY,
              pm1_ratio REAL,
              pm25_ratio REAL,
              local_aqi INTEGER,
              us_aqi INTEGER,
              cn_aqi INTEGER,
              err_msg TEXT)""")
    for col in 'local', 'us', 'cn':
        c.execute("""CREATE INDEX idx_{0}_aqi ON history ({0}_aqi)""".format(
            col))

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
    pm1_ratio, pm25_ratio, local_aqi, us_aqi, cn_aqi = [-1] * 5
    err_msg = None
    job = gevent.spawn(get_aqi)
    try:
        pm1_ratio, pm25_ratio = get_local_sample()
        local_aqi = lowratio2aqi(pm1_ratio - pm25_ratio)
    except Exception as exc:
        err_msg = 'failed to sample locally: {}'.format(exc)

    job.join()
    try:
        if job.successful():
            us_aqi, cn_aqi = job.value
        else:
            raise job.exception
    except Exception as exc:
        if err_msg is None:
            err_msg = ''
        err_msg = 'failed to retrieve AQI: {}'.format(exc)


    conn = get_db_conn()
    conn.cursor().execute(
        """INSERT INTO history VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (time, pm1_ratio, pm25_ratio, local_aqi, us_aqi, cn_aqi, err_msg))
    conn.commit()


if __name__ == '__main__':
    insert_db_entry()

