"""
Decay is an abstract parameter that with each retrieval (Decay.value) decays towards asymptote.
"""

import numpy as np
from matplotlib import pyplot as plt
from collections.abc import Iterable
from itertools import takewhile


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


class Ticker:
    def __init__(self):
        self.ticker = 0
        self.registry = []

    def tick(self, n=None):
        n = n or 1
        self.ticker += n

    def flush(self):
        self.registry.append(self.ticker)
        self.ticker = 0

    @property
    def last_ones(self):
        return len(tuple(takewhile(lambda x: x == 1, self.registry[::-1])))


class Adapter:

    """
    development note: nudge reduction is experimental
    to remove this feature:
        remove: STD_NUDGE_ASYMPTOTE
        remove: self.nudge_rate = Hyperbola(self.STD_NUDGE, 0, self.STD_NUDGE_ASYMPTOTE)
        remove: self.nudge_rate.adjust_rate(0, self.STD_NUDGE, 1, self.STD_NUDGE * 0.7)
        alter:
            next_nudge = mean_fails + \
                         (direction * self.nudge_rate.value(self.step) * std_fails) + \
                         (direction * last_ones * 0.5 * std_fails)  # surplus for multiple single attempt fails
        to:
            next_nudge = mean_fails + \
                         (direction * self.STD_NUDGE * std_fails) + \
                         (direction * last_ones * 0.5 * std_fails)  # surplus for multiple single attempt fails

        alter:
            STD_NUDGE = 3
        to:
            STD_NUDGE = 2
    """

    N_WARM_UP = 1  # number of steps before adaptation is used in next value prediction
    N_DECAY = 5  # number of nudges at which rate will become very small (0.1% drop over one step)
    STD_NUDGE = 3  # factor the fail distribution std will be multiplied by when deciding the next nudge value
    # STD_NUDGE will be subject tu hyperbolic decrease towards asymptote
    STD_NUDGE_ASYMPTOTE = 1.1  # the asymptote for deceasing STD_NUDGE
    # STD_NUDGE_ASYMPTOTE must be > STD_ASYMPTOTE
    STD_ASYMPTOTE = 1  # factor the fail distribution std will be multiplied by when deciding the next acymptote

    def __init__(self, decay):
        self.decay = decay
        self.decay_rate = Hyperbola(-1, 0, 1)
        self.decay_rate.adjust_rate(0, self.decay.rate, self.N_DECAY, 0.999)

        # nudge reduction curve
        self.nudge_rate = Hyperbola(self.STD_NUDGE, 0, self.STD_NUDGE_ASYMPTOTE)
        self.nudge_rate.adjust_rate(0, self.STD_NUDGE, 1, self.STD_NUDGE * 0.7)

        self.next_asymptote = None
        self.next_nudge = None
        self.to_be_set_decay_rate = None
        self.fails = []

    @property
    def step(self):
        return len(self.fails) - self.N_WARM_UP

    def adjust(self):
        """
        calculates next nudge and next asymptote values
        from the probbability of fail values
        """
        if self.fails:
            mean_fails = np.mean(np.array(self.fails))
            std_fails = np.std(self.fails)
        else:
            mean_fails = 0
            std_fails = 0

        last_ones = self.decay.ticker.last_ones
        direction = self.decay.c
        user_asymptote = self.decay.init_asymptote

        if self.step < 0:
            next_asymptote = self.decay.asymptote
            next_nudge = self.decay.start
        else:
            next_nudge = mean_fails + \
                         (direction * self.nudge_rate.value(self.step) * std_fails) + \
                         (direction * last_ones * 0.5 * std_fails)  # surplus for multiple single attempt fails
            next_asymptote = mean_fails + (direction * self.STD_ASYMPTOTE * std_fails)

        if next_nudge == next_asymptote:
            all_interval = self.decay.start, self.decay.init_asymptote, *self.fails
            mean_all_interval = np.mean(all_interval)
            std_all_interval = np.std(all_interval)
            next_nudge = mean_all_interval + \
                (direction * 1 * std_all_interval) + \
                (direction * last_ones * 0.5 * std_all_interval)  # surplus for multiple single attempt fails

            if direction == 1:
                next_asymptote = max(
                    user_asymptote,
                    mean_all_interval -
                    (direction * 2 * std_all_interval) -
                    (direction * last_ones * 0.5 * std_all_interval)
                )  # surplus for multiple single attempt fails
            else:
                next_asymptote = min(
                    user_asymptote,
                    mean_all_interval -
                    (direction * 2 * std_all_interval) -
                    (direction * last_ones * 0.5 * std_all_interval)
                )  # surplus for multiple single attempt fails


        self.next_nudge = next_nudge
        self.next_asymptote = next_asymptote
        print(
            f'mean_fails {mean_fails}\t\tnext_nudge '
            f'{self.next_nudge}\t\tnext asymptote {self.next_asymptote}\t\t last ones {last_ones}')

        # DELAY CURVE
        if self.step >= 0:
            self.to_be_set_decay_rate = self.decay_rate.value(self.step)
        # rate curve needs no adjustment as the only parameter defining it is self.N_DECAY
        # because it always tends to 1 (100% of the previous rate

    def adapt(self):
        """
        this is called by Decay if conditions are met
        """
        if self.step < 0:
            raise RuntimeError(f'adaptation has been called before warm-up has completed')
        self.decay.ticker.flush()
        self.fails.append(self.decay.previous)
        self.adjust()

        # adjusting asymptote
        self.decay.curve.v = self.next_asymptote
        # nudging must be done here as adapte must controll all the prformance of the Decay curve
        self.decay.curve.shift_h(self.decay.step, self.next_nudge)
        self.decay.last_nudge = self.next_nudge
        # adjusting rate
        self.decay.rate = self.to_be_set_decay_rate

        self.decay._nudged = True


class Decay:
    """
        Decay is an abstract factor that delivers a value approaching the asymptote along the hyperbolic curve.
        The instantiation parameters are:
            start - an initial value
            asymptote - the target value - never to be reached
            rate - initial rate value - the percentage of initial value to be reached in the next step.
                The subsequent steps will return different values depending on the initial value and the asymptote,
                The reate of the values rate (towards the asymptote) is steered by the first step rate.
                eg: If initial value is 4, asymptote 0, and rate is 0.5, the second value will be 2,
                and the subsequent values, will follow the hiperbolic curve towards 0.
                The curve first two points are (0,4) and (1,2).
            nudge: Optional - the percent of the fail value (the value at witch a nudge was dane
                the delivered (next) value will be insreased by, so it is further away from the asymptote.
                eg:
                In the descending rate curve:
                    if the last delivered value was 3 and nudge is set to 0.1, the next delivered value will be 3.3
                In the ascending rate curve:
                    if the last delivered value was 3 and nudge is set to 0.11, the next delivered value will be 2.7
                The safest and usually efficient value is 1 (100%)
        methods:
            deliver(n: int) - delivers two tuples of length n:
                first one is an array of steps numbers
                second one is an array of the calculated values
                and also makes n steps

            nudge(by: float) - the next delivered value will be altered,
                by the passed value (or the nudge value set at instantiation). See parameter nudge.

        attributes:
            value: current value
            step: current step

        work cycle is
        deliver value
        ↓
        ↓ (nudge)
        ↓
        record las fail (in Decay.adapter.fails)
        ↓
        plan nudge and asymptote or use one delivered by user (at adapter warm-up)
        ↓
        deliver nudge and set asymptote
        ↓
        continue delivering values

        """
    UNHOOK = 1000  # number of steps neede to onhook the asymptote

    def __init__(self, start, asymptote=0, rate=0.5, nudge=1, adapt=True):
        self.start = start
        self.adapt = adapt
        self.nudge_by = nudge or 0
        self._step = 0
        self._nudged = False
        self.ticker = Ticker()
        self.last_nudge = start

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

        # shaping the curve
        self.curve = Hyperbola(self.c, 1, asymptote)  # h = 1 so the value for step 0 = v + 1
        self.asymptote = self.init_asymptote = asymptote
        self.curve.shift_h(0, start)
        self.rate = rate
        # setting adapter
        self.adapter = Adapter(self)
        self.last_unhook = 2

    @property
    def value(self):
        return self.curve.value(self.step)

    @property
    def previous(self):
        return self.curve.value(max(self.step - 1, 0))

    @property
    def step(self):
        return self._step

    @property
    def rate(self):
        return self._rate

    @rate.setter
    def rate(self, x) -> None:
        self._rate = x
        self.solve_rate(x)

    @property
    def asymptote(self):
        return self.curve.v

    @asymptote.setter
    def asymptote(self, val):
        self.curve.v = val

    def solve_rate(self, drop) -> None:
        if not 0 < drop < 1:
            raise ValueError(
                f'one_step_drop is expected to be a percentage of value drop after one step, and must be  0 < x < 1. '
                f'Got {drop}')
        current_y = self.curve.value(self.step)
        current_x = self.step
        after_step_y = current_y - ((current_y - self.asymptote) * (1 - drop))
        after_step_x = self.step + 1
        self.curve.adjust_rate(current_x, current_y, after_step_x, after_step_y)

    def deliver(self, n=None, plot=False, xs=False):
        """
        Delivers n coordinates as a tuple of numpy array : (array(xs), array(ys))
        (the array lengths equal to n)
        and makes n steps ahead
        :param n:
        :param plot:
        :param xs: bool if True a tuple will be returned (xs, ys). If False just ys will be returned.
        :return:
        """
        if n is None:
            n = 1
            coor = self.step, self.value
        else:
            xs_array = np.arange(n) + self._step
            coor = self.curve.coordinates(xs_array)
            if plot:
                plt.plot(*coor, '.')

        self._nudged = False
        self._step += n
        self.ticker.tick(n)

        if not xs:
            coor = coor[1]
        return coor

    def nudge(self):
        if self.adapt and self.adapter.step >= 0:
            self.adapter.adapt()
        else:
            required_y = self.previous + (self.c * abs(self.previous - self.curve.v))
            return self.nudge_to_value(required_y)

    def nudge_by_percent(self, percent):
        """
        nudges the value by the percent of the last value
        :param percent:  0 < percent < 1
        :return:
        """
        relative = self.previous - self.curve.v
        value = self.c * abs(relative * percent)
        self.nudge_by_value(value)

    def nudge_by_value(self, value):
        required_y = self.previous + value
        self.nudge_to_value(required_y)

    def nudge_to_value(self, value):
        if self._nudged:
            raise UserError('Decay can not be nudged twice at the same step. To achieve bigger nudge set nudge value.')

        self.ticker.flush()
        self.adapter.fails.append(self.previous)

        self.curve.shift_h(self.step, value)
        self.last_nudge = value
        self._nudged = True

    def __repr__(self):
        if self.c == 1:
            mode = 'descending'
        else:
            mode = 'ascending'
        return f'<Decay [{mode}] current:{self.value}, asymptote:{self.curve.v}'
