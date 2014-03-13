#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# $File: plot.py
# $Date: Thu Mar 13 19:14:33 2014 +0800
# $Author: jiakai <jia.kai66@gmail.com>

import pyximport
pyximport.install()

import datafilter
from sample_and_record import get_db_conn

import matplotlib.pyplot as plt
from matplotlib import dates

import sys
import os.path
from datetime import datetime
from collections import namedtuple
from copy import deepcopy


class AQSample(object):
    __slots__ = ['time', 'local', 'us', 'cn']

    def __init__(self, time, local, us, cn):
        for i in self.__slots__:
            setattr(self, i, locals()[i])


def load_sample():
    result = list()
    cursor = get_db_conn().cursor()
    for i in list(cursor.execute('SELECT * FROM history')):
        if i['local_conc'] > 0 and i['us_conc'] > 0 and i['cn_conc'] > 0:
            result.append(AQSample(
                i['time'], i['local_conc'], i['us_conc'], i['cn_conc']))

    return result


def get_time_plot(plot_ax):
    fig = plt.figure()
    ax = fig.add_subplot(111)

    plot_ax(ax)

    #ax.xaxis.set_major_locator(dates.HourLocator(interval=8))
    ax.xaxis.set_major_formatter(dates.DateFormatter('%m/%d %H:%M'))
    ax.set_ylim(bottom=0)

    plt.legend(loc='best')
    plt.xticks(rotation='vertical')
    plt.subplots_adjust(bottom=.3)


def main(output_dir):
    orig = load_sample()

    filtered = deepcopy(orig)
    datafilter.rescale(filtered)
    datafilter.smooth_gaussian(filtered)

    avg = deepcopy(orig)
    datafilter.smooth_average(avg, 3600)
    avg1 = [avg[0]]
    for i in avg[1:]:
        if i.time - avg1[-1].time >= 3600:
            avg1.append(i)
    avg = avg1

    time = dates.date2num([datetime.fromtimestamp(i.time) for i in orig]) 

    def plot_local(ax):
        ax.plot(time, [i.local for i in filtered], label='filtered')
        ax.plot(time, [i.local for i in orig], label='original')

    def plot_compare(ax):
        ax.plot(time, [i.local for i in filtered], label='filtered')
        ax.plot(time, [i.us for i in orig], label='us')
        ax.plot(time, [i.cn for i in orig], label='cn')

    fig = plt.figure()
    ax = fig.add_subplot(111)

    ax.plot([i.local for i in avg], [i.us for i in avg], '.')
    plt.savefig(os.path.join(output_dir, 'scatter.png'))

    get_time_plot(plot_local)
    plt.savefig(os.path.join(output_dir, 'local.png'))

    get_time_plot(plot_compare)
    plt.savefig(os.path.join(output_dir, 'compare.png'))
    plt.show()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('usage: {} <output dir>'.format(sys.argv[0]))
    main(sys.argv[1])
