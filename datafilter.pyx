#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# $File: datafilter.pyx
# $Date: Thu Mar 13 19:08:46 2014 +0800
# $Author: jiakai <jia.kai66@gmail.com>

cimport cython
from libc.stdlib cimport malloc, free
from libc.math cimport exp

cdef:
    int FILTER_SIGMA = 1800
    int FILTER_RADIUS = 3 * FILTER_SIGMA
    double FILTER_SIGMA_INV = 1.0 / FILTER_SIGMA

    double gaussian(double x):
        x *= FILTER_SIGMA_INV
        return exp(-0.5 * x * x)

    struct SamplePoint:
        int time
        double val


def smooth_gaussian(pysample):
    cdef:
        size_t current, t, nr_sample
        SamplePoint* sample
        int cur_time, head_time, tail_time
        double weight_sum, val_sum, w

    sample = <SamplePoint*>malloc(len(pysample) * cython.sizeof(SamplePoint))

    if sample is NULL:
        raise MemoryError()

    current = 0
    for i in pysample:
        sample[current].time = i.time
        sample[current].val = i.local
        current += 1

    nr_sample = current
    current = 0
    for i in pysample:
        cur_time = sample[current].time
        head_time = cur_time - FILTER_RADIUS
        tail_time = cur_time + FILTER_RADIUS
        weight_sum = gaussian(0)
        val_sum = weight_sum * sample[current].val
        t = current - 1
        while t < nr_sample and sample[t].time >= head_time:
            w = gaussian(sample[t].time - cur_time)
            weight_sum += w
            val_sum += w * sample[t].val
            t -= 1

        t = current + 1
        while t < nr_sample and sample[t].time <= tail_time:
            w = gaussian(sample[t].time - cur_time)
            weight_sum += w
            val_sum += w * sample[t].val
            t += 1

        i.local = val_sum / weight_sum
        current += 1

    free(sample)


def smooth_average(pysample, length):
    length /= 2
    cdef:
        size_t current, nr_sample, head, tail
        SamplePoint* sample
        double cur_val_sum
        int cur_time, head_time, tail_time

    sample = <SamplePoint*>malloc(len(pysample) * cython.sizeof(SamplePoint))

    if sample is NULL:
        raise MemoryError()

    current = 0
    for i in pysample:
        sample[current].time = i.time
        sample[current].val = i.local
        current += 1

    nr_sample = current
    current = 0
    head = 0
    tail = 0
    cur_val_sum = 0
    for i in pysample:
        cur_time = sample[current].time
        head_time = cur_time - length
        tail_time = cur_time + length

        while sample[head].time < head_time:
            cur_val_sum -= sample[head].val
            head += 1

        while tail < nr_sample and sample[tail].time < tail_time:
            cur_val_sum += sample[tail].val
            tail += 1

        i.local = cur_val_sum / (tail - head)
        current += 1

    free(sample)

def rescale(sample):
    """min sum((i.local * x - i.us)^2)"""

    sum_a = sum(i.local for i in sample)
    sum_b = sum(i.us for i in sample)
    x = sum_b / sum_a
    print 'rescale:', x

    for i in sample:
        i.local *= x
