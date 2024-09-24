from collections.abc import Iterable, Generator
from typing import Tuple


DLI_MESSAGE = 'Different length iterables.'


def zipeven(*iterables: Iterable) -> Generator:
    """
    this does the same thig as zip bur raises if iterables lengths are uneven
    :return:
    """

    l = 0
    gen_detected = 0
    non_gen_detected = 0

    for ind, it in enumerate(iterables):
        try:
            it_l = len(it)
            if non_gen_detected > 0 and it_l != l:
                raise ValueError(DLI_MESSAGE)
            l = it_l
            non_gen_detected += 1

        except TypeError:
            if isinstance(it, Generator):
                gen_detected += 1
                continue
            else:
                raise NotImplemented from TypeError(f'{type(it)}')

    if gen_detected:
        return _zip_with_generators(*iterables)
    else:
        return zip(*iterables)


def _zip_with_generators(*iterables):
    iterables = [iter(it) for it in iterables]
    safe = 0
    while True:
        safe += 1
        if safe > 5:
            break
        yieldable = []
        for ind, it in enumerate(iterables):
            try:
                yieldable.append(next(it))
            except StopIteration:
                if ind == 0:
                    return _deplete_others(*iterables[1:])  # check if others end in the next step too
                else:
                    raise ValueError(DLI_MESSAGE)

        yield tuple(yieldable)
        # not need to break while loop as this happens at the StopIteration


def _deplete_others(*iterables):
    for it in iterables:
        try:
            next(it)  # expected to raise StopIteration
            raise ValueError(DLI_MESSAGE)
        except StopIteration:
            continue
    return  # If all iterables end at the same time
