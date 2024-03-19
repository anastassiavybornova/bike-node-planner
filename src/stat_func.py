import matplotlib.pyplot as plt
import contextily as cx

def rgb2hex(rgb_string):
    return '#%02x%02x%02x' % tuple([int(n) for n in rgb_string.split(",")])

def _get_midpoint(t):
    return t[0] + (t[1]-t[0])/2