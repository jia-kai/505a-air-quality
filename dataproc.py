#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# $File: dataproc.py
# $Date: Tue Mar 11 00:25:03 2014 +0800
# $Author: jiakai <jia.kai66@gmail.com>

import math

class LinearFunction(object):
    k = None
    b = None

    def __init__(self, x0, y0, x1, y1):
        self.k = (y1 - y0) / (x1 - x0)
        self.b = y0 - self.k * x0
        assert abs(self.eval(x0) - y0) < 1e-5
        assert abs(self.eval(x1) - y1) < 1e-5

    def eval(self, x):
        return self.k * x + self.b

AQI_TABLE = [
    [12.1, 51],
    [35.5, 101],
    [55.5, 151],
    [150.5, 201],
    [250.5, 301],
    [350.5, 401],
    [500, 500]
]

# pcs: m^{-3}
lowratio2pcs = LinearFunction(0, 0, 9.8e-2, 6000/283e-6).eval

# ug/m^3 * volume
_PCS2CONCENTRATION_COEFF = 1.65e6/1e-6 * math.pi*4/3*(2.5e-6/2)**3
def pcs2concentration(pcs):
    """ug/m^3"""
    return _PCS2CONCENTRATION_COEFF * pcs


def concentration2aqi(con):
    if con < 0:
        return con
    iprev = [0, 0]
    for i in AQI_TABLE:
        if con < i[0]:
            return LinearFunction(iprev[0], iprev[1], i[0], i[1]).eval(con)
        iprev = i
    return con

def aqi2concentration(aqi):
    if aqi < 0:
        return aqi
    iprev = [0, 0]
    for i in AQI_TABLE:
        if aqi < i[1]:
            return LinearFunction(iprev[1], iprev[0], i[1], i[0]).eval(aqi)
        iprev = i
    return aqi

def lowratio2concentration(lr):
    return pcs2concentration(lowratio2pcs(lr))

def lowratio2aqi(lr):
    return concentration2aqi(lowratio2concentration(lr))


