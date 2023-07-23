import matplotlib
from matplotlib import pyplot as plt
import numpy as np

start = 2
nudge = 1
decay310 = 1 # decay over 3 and 10 steps
minimum = 0

from collections.abc import Iterable


class Hyperbola:
    def __init__(self, c, h, v):
        self.c = c
        self.h = h
        self.v = v

    def coordinates(self, steps):
        if isinstance(steps, (float, int)):
            steps = [steps]
        elif isinstance(steps, Iterable) and all(isinstance(x, (float, int, np.number)) for x in steps):
            pass
        else:
            raise TypeError(f'wrong: {steps}')

        return np.array(steps), np.array([self.value(s) for s in steps])

    def value(self, x):
        return (self.c / (x + self.h)) + self.v

    def plot(self, steps):
        return plt.plot(*self.coordinates(steps), '.')


class Decay:
    def __init__(self, start=1, minimum=0, decay=0.5):
        self.start = start
        self.minimum = minimum
        self.step = 0
        self.curve = Hyperbola(1, 1, minimum)

        nudge = start - 1
        self.nudge(nudge)
        self.decay = decay

    def nudge(self, by):
        current_y = self.curve.value(self.step)
        required_y = current_y + by
        self.curve = Hyperbola(self.curve.c, self.solve_h(required_y), self.curve.v)

    @property
    def decay(self):
        return self._decay

    @decay.setter
    def decay(self, x):
        self._decay = x
        c, h = self.solve_decay(x)
        self.curve = Hyperbola(c, h, self.minimum)

    def solve_h(self, desired_y) -> float:
        return invert((desired_y - self.curve.v) / self.curve.c) - self.step

    def solve_decay(self, one_step_drop) -> tuple:
        if not 0 < one_step_drop < 1:
            raise ValueError(
                f'one_step_drop is expected to be a percentage of value drop after one step, and must be  0 < x < 1. Got {one_step_drop}')
        current_y = self.curve.value(self.step)
        current_x = self.step
        after_step_y = current_y * one_step_drop
        after_step_x = self.step + 1
        desired_h = ((after_step_y * after_step_x) - (current_x * current_y) + (
                    current_x * self.curve.v) + self.curve.v) / (current_y - after_step_y - self.curve.v)
        desired_c = (current_y - self.curve.v) * (current_x + desired_h)
        return desired_c, desired_h

    def deliver(self, n=1, plot=False):
        xs = np.arange(n) + self.step
        self.step += n
        coor = self.curve.coordinates(xs)
        if plot:
            plt.plot(*coor, '.')

        return coor


def invert(v):
    if v == 0:
        return 0
    else:
        return v ** -1


xs = range(10)

h = Decay(start=3, decay=0.6)
x1, y1 = h.deliver(10, True)
h.nudge(1)
h.decay = 0.7
x2, y2 = h.deliver(10, True)
x= np.concatenate((x1, x2))
y = np.concatenate((y1, y2))
plt.plot(x, y)


def trial(nudges=3):
    d = Decay(start=1, decay=0.2)
    xs = np.array([])
    ys = np.array([])
    decays = []
    d_ch = 0.2
    for n in range(nudges):
        dx, dy = d.deliver(10)
        xs = np.concatenate((xs, dx))
        ys = np.concatenate((ys, dy))
        d.nudge(1)
        d.decay = d.decay + (d_ch * d.decay / max(n, 1))

        dd = [d.decay] * 10
        decays.extend(dd)
    plt.plot(xs, ys)
    plt.plot(xs, decays)

trial(20)