#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# $File: update_db.py
# $Date: Tue Mar 11 00:07:07 2014 +0800
# $Author: jiakai <jia.kai66@gmail.com>

import sys
sys.path.append('..')

from sample_and_record import get_db_conn, init_db
from dataproc import aqi2concentration, lowratio2concentration

def update_db():
    conn = get_db_conn()
    conn.cursor().execute("""ALTER TABLE history RENAME TO history00""")
    init_db(conn)

    c = conn.cursor()
    for i in list(c.execute('SELECT * from history00')):
        print i[0]
        c.execute(
            """INSERT INTO history VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (i[0], i[1], i[2],
             lowratio2concentration(i[1] - i[2]),
             aqi2concentration(i[4]),
             aqi2concentration(i[5]),
             i[6]))

    conn.commit()

if __name__ == '__main__':
    update_db()

