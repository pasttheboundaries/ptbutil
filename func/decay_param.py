"""
Decay is an abstract parameter that with each retrieval (Decay.value) decays towards asymptote.
"""

import numpy as np
from matplotlib import pyplot as plt
from collections.abc import Iterable
from collections import namedtuple


def invert(v):
    if v == 0:
        return 0
    else:
        return v ** -1


class UserError(ValueError):
    pass


class Hyperbola:
    """
    this is a function

          c
    y = ------ + v
        x - h

    which is a hyperbola function

    c is a parameter that decides about  the curvature of the hyperbola and also a +/1 flip
        when c is positive y will be decreaseing for x > h
    h decides about horizontgal shift and vertical asymptote.
       as h goes up the curve shifts to the left
    v decides about vertical shift and horizontal asymptote
        as h goes up the whole curve shifts up


    """
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

    def plot(self, xs, marker='.', dpi=300, grid=True):

        plt.figure(dpi=dpi, layout='tight')
        if grid:
            plt.grid()
        return plt.plot(*self.coordinates(xs), marker)

    def shift_h(self, x, y) -> None:
        """
        shifts hyperbola horizontally so the same shape is maintained and crossing (x,y)
        :param x: float
        :param y: float
        :return: None
        """
        self.h = invert((y - self.v) / self.c) - x

    def adjust_rate(self, x1, y1, x2, y2) -> None:
        """
        adjusts c and h so the curvature changes and the curve passes (x1, y1) and (x2, y2)
        Does not alter the asymptote (v)
        :return: None
        """
        desired_h = ((x2 * y2) - (x2 * self.v) - (x1 * y1) + (x1 * self.v)) / (y1 - y2)
        desired_c = (y1 - self.v) * (x1 + desired_h)
        self.h = desired_h
        self.c = desired_c


class Adapter:

    N_WARM_UP = 3
    N_DECAY = 5  # number of nudges at which decay will become very small (0.1% drop over one step)
    N_ASYMPTOTE = 5  # steps needed to asymptote reach
    N_NUDGE = 5  # steps needed to decrease nudge
    ASYMPTOTE_BACKUP_RATE = 0.9  # factor to multiply current asymptote if above fail value
    NUDGE_DECAY_BACKUP_RATE = 0.1  # facter to increse nudge decay if below fail value
    NUDGE_EXCESS = 0.05  # above fail value

    def __init__(self, decay):
        self.decay = decay
        self.registry = list()
        self.decay_rate_curve = Hyperbola(-1, 0, 1)
        self.decay_rate_curve.adjust_rate(0, self.decay.decay, self.N_DECAY, 0.999)

        self.decay_asymptote_curve = Hyperbola(-self.decay.c, 0, self.decay.start)
        self.decay_asymptote_curve.adjust_rate(self.step, self.decay.asymptote,
                                               self.step + self.N_ASYMPTOTE, self.decay.start * 0.99)

        self.decay_nudge_curve = Hyperbola(self.decay.c, 0, 0)
        self.decay_nudge_curve.adjust_rate(self.step, self.decay.start,
                                           self.step + self.N_NUDGE, self.decay.start * self.decay.nudge_by * 0.01)
        self.to_be_set_decay_asymptote = None
        self.to_be_set_nudge_value = None
        self.to_be_set_decay_rate = None

    def record(self, rec):
        if not isinstance(rec, NudgeRecord):
            raise TypeError('must be NudgeRecord')
        self.registry.append(rec)
        self.adjust()
        if self.step >= 0:  # active since n = 0
            return True
        else:
            return False

    @property
    def step(self):
        return len(self.registry) - self.N_WARM_UP  # 0 is after N_WARM_UP steps od the owner Decay

    def adjust(self):
        user_asymptote = self.decay.asymptote
        # [-self.N_WARM_UP:]
        mean_past_fail_value = np.mean(np.array([r.y1 for r in self.registry]))
        mean_past_nudge_value = np.mean(np.array([r.y2 for r in self.registry]))
        # expected_v = (mean_past_nudge_value + mean_past_fail_value) / 2   # expected fail value = optimum decay value
        #                                                         # halfway between nudge and fail value
        expected_v = mean_past_fail_value

        # ASYMPTOTE CURVE
        # calculations
        next_decay_asymptote = self.decay_asymptote_curve.value(self.step)  # asymptote to be set at this nudge
        relative_diff = abs(expected_v - user_asymptote)

        target_asymptote = expected_v
        target_nearly_asymptote = expected_v - self.decay.c * relative_diff * 0.05  # target nearly asymptote - 5%

        if self.step < 0:
            # this keeps decay_asymptote_curve at the user set value while warming up
            # otherwise it would flip the curve as to_be_set_decay_asymptote might be above expected_v during warmup
            next_decay_asymptote = user_asymptote
        else:
            pass

            # overshoot correction
            to_b_set_v_diff = abs(next_decay_asymptote - user_asymptote)
            target_diff = abs(target_nearly_asymptote - user_asymptote)
            if to_b_set_v_diff >= target_diff:
                next_decay_asymptote = user_asymptote + self.decay.c * target_diff * self.ASYMPTOTE_BACKUP_RATE
        self.to_be_set_decay_asymptote = next_decay_asymptote

        # setting
        self.decay_asymptote_curve.v = target_asymptote
        self.decay_asymptote_curve.adjust_rate(self.step, next_decay_asymptote,
                                               self.step + self.N_ASYMPTOTE, target_nearly_asymptote)

        # NUDGE CURVE (absolute values)
        # calculations
        to_be_set_nudge_value = self.decay_nudge_curve.value(self.step)
        nudge_asymptote = expected_v + self.decay.c * abs(expected_v) * self.NUDGE_EXCESS
        nudge_nearly_asymptote = expected_v + self.decay.c * abs(expected_v) * (self.NUDGE_EXCESS * 2)
        last_fail = self.registry[-1].y1

        if abs(to_be_set_nudge_value - user_asymptote) < abs(last_fail - user_asymptote):
            to_be_set_nudge_value = last_fail + self.decay.c * abs(last_fail) * self.NUDGE_DECAY_BACKUP_RATE
        else:
            pass
        self.to_be_set_nudge_value = to_be_set_nudge_value
        # setting
        self.decay_nudge_curve.v = nudge_asymptote
        self.decay_nudge_curve.adjust_rate(self.step, mean_past_nudge_value, self.step + self.N_NUDGE, nudge_nearly_asymptote)

        # DELAY CURVE
        # setting
        self.to_be_set_decay_rate = self.decay_rate_curve.value(self.step)
        # decay curve needs no adjustment as the only parameter defining it is self.N_DECAY
        # because it always tends to 1 (100% of the previous decay

        # print(f'___ Decay step {self.decay.step - 1}; Adapter step {self.step}; Will adapt : {self.step >=0}\n'
        #       f'--- Failed at {self.decay.previous}; Current nudge {self.to_be_set_nudge_value}; expected_v:{expected_v}\n '
        #       f'--- current Decay {self.decay.value}; current Decay asymptote {self.to_be_set_decay_asymptote}; planned Decay asymptote {target_asymptote}\n'
        #       f'--- Decay rate {self.decay_rate_curve.value(self.to_be_set_decay_rate)}; Decay rate asymptote {self.decay_rate_curve.v}\n'
        #       f'--- next nudge {self.to_be_set_nudge_value}; Next nudge {mean_past_nudge_value}; Nudges asymptote {nudge_asymptote}')

    def adapt(self):
        """
        this is called by Decay if conditions are met
        :return:
        """
        self.record(NudgeRecord(self.decay.step - self.decay._last_nudge_step, self.decay.previous, self.to_be_set_nudge_value))
        # adjusting asymptote
        self.decay.curve.v = self.to_be_set_decay_asymptote
        # nudging must be done here as adapte must controll all the prformance of the Decay curve
        self.decay.curve.shift_h(self.decay.step, self.to_be_set_nudge_value)
        # adjusting decay
        self.decay.decay = self.to_be_set_decay_rate


class NudgeRecord(namedtuple('NudgeRecord', field_names='steps y1 y2')):
    pass


class Decay:
    """
        Decay is an abstract factor that delivers a value approaching the asymptote along the hyperbolic curve.
        The instantiation parameters are:
            start - an initial value
            asymptote - the target value - never to be reached
            decay - initial decay value - the percentage of initial value to be reached in the next step.
                The subsequent steps will return different values depending on the initial value and the asymptote,
                The reate of the values decay (towards the asymptote) is steered by the first step decay.
                eg: If initial value is 4, asymptote 0, and decay is 0.5, the second value will be 2,
                and the subsequent values, will follow the hiperbolic curve towards 0.
                The curve first two points are (0,4) and (1,2).
            nudge: Optional - the percent of the fail value (the value at witch a nudge was dane
                the delivered (next) value will be insreased by, so it is further away from the asymptote.
                eg:
                In the descending decay curve:
                    if the last delivered value was 3 and nudge is set to 0.1, the next delivered value will be 3.3
                In the ascending decay curve:
                    if the last delivered value was 3 and nudge is set to 0.11, the next delivered value will be 2.7
                The safest and usually efficient value is 1 (100%)
        methods:
            deliver(n: int) - delivers two tuples of length n:
                first one is an array of steps numbers
                second one is an array of the calculated values
                and also makes n steps

            nudge(by: float) - the delivered value will be altered,
                by the passed value (or the nudge value set at instantiation). See parameter nudge.

        attributes:
            value: current value
            step: current step

        """

    def __init__(self, start, asymptote=0, decay=0.5, nudge=1, adapt=True):
        self.start = start
        self.asymptote = asymptote
        nudge = nudge or 0
        self._step = 0
        self._last_nudge_step = self.step
        self.adapt = adapt
        self._nudged = False

        if start > asymptote:
            self.c = 1
            # if nudge <= 0:
            #     raise ValueError('For descending Decay nudge must be > 0')
        elif start < asymptote:
            self.c = -1
            # if nudge >= 0:
            #     raise ValueError('For descending Decay nudge must be < 0')
        else:
            raise ValueError('start valaue can not be equal to asymptote.')

        self.nudge_by = nudge

        # shaping the curve
        self.curve = Hyperbola(self.c, 1, asymptote)  # h = 1 so the value for step 0 = v + 1
        self.curve.shift_h(0, start)
        self.decay = decay
        # setting adapter
        self.adapter = Adapter(self)

    @property
    def value(self):
        return self.curve.value(self.step)

    @property
    def previous(self):
        return self.curve.value(self.step-1)

    @property
    def step(self):
        return self._step

    @property
    def decay(self):
        return self._decay

    @decay.setter
    def decay(self, x) -> None:
        self._decay = x
        self.solve_decay(x)

    def solve_decay(self, drop) -> None:
        if not 0 < drop < 1:
            raise ValueError(
                f'one_step_drop is expected to be a percentage of value drop after one step, and must be  0 < x < 1. '
                f'Got {drop}')
        current_y = self.curve.value(self._step)

        current_x = self._step
        if self.c == 1:
            diff = current_y - self.asymptote
            after_step_y = current_y - (diff * (1 - drop))
        else:
            diff = self.asymptote - current_y
            after_step_y = current_y + (diff * (1 - drop))

        after_step_x = self._step + 1
        self.curve.adjust_rate(current_x, current_y, after_step_x, after_step_y)

    def deliver(self, n=None, plot=False):
        """
        Delivers n coordinates as a tuple of numpy array : (array(xs), array(ys))
        (the arrays length is equal to n)
        and makes n steps ahead
        :param n:
        :param plot:
        :return:
        """
        if n is None:
            return self.deliver(1, plot=plot)[1][0]
        xs = np.arange(n) + self._step
        self._step += n
        self._nudged = False
        coor = self.curve.coordinates(xs)
        if plot:
            plt.plot(*coor, '.')

        return coor

    def nudge(self, by=None):
        by = by or self.nudge_by
        if not 0 < by:
            raise ValueError(
                f'nudge by is expected to be a percentage of value ath wich the nudge is done, and must be  0 < x . '
                f'Where 1 = 100%. Got {by}')
        if not by:
            raise ValueError('Nudge value must be passed or declared at instantiation.')
        self.nudge_by_percent(by)

    def nudge_by_percent(self, percent):
        current_y = self.curve.value(self.step)
        # print(f'current value = {current_y}')
        value = self.c * abs(current_y * percent)
        self.nudge_by_value(value)

    def nudge_by_value(self, value):
        # print(f'nudging by value {value}')
        current_y = self.curve.value(self.step)
        required_y = current_y + value
        # print(f'nudging to value {required_y}')
        self.nudge_to_value(required_y)

    def nudge_to_value(self, value):
        if self._nudged:
            raise UserError('Decay can not be nudged twice in row. To achieve bigger nudge set nudge value.')
        adaptation_warmed_up = self.adapter.step >= 0
        if adaptation_warmed_up and self.adapt:
            self.adapter.adapt()
        else:
            next_nudge_value = value
            self.adapter.record(NudgeRecord(self.step - self._last_nudge_step, self.previous, next_nudge_value))
            self.curve.shift_h(self.step, next_nudge_value)

        self._last_nudge_step = self.step
        self._nudged = True

    def __repr__(self):
        if self.c == 1:
            mode = 'descending'
        else:
            mode = 'ascending'
        return f'<Decay [{mode}] current:{self.value}, asymptote:{self.curve.v}'
