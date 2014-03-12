#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# $File: datafilter.pyx
# $Date: Thu Mar 13 00:19:26 2014 +0800
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

def filter_samples(pysample):
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
