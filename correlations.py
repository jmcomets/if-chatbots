import itertools as it

import numpy as np

def compute_present_classes_by_timestamp(data_by_nickname):
    time_classes = None
    classes = {}

    for i, (nickname, timestamps) in enumerate(data_by_nickname.items()):
        classes[i] = nickname
        C = np.zeros(len(timestamps))
        C.fill(i)

        T = np.array(timestamps)

        # compute local derivatives
        DT = np.array([0] + list(map(lambda x: x[0] - x[1], zip(T[1:], T[:-1]))))

        # TODO: apply smoothing ?

        # low derivative -> presence
        avg = np.average(DT)
        P = np.vectorize(lambda x: x < avg, otypes=[np.bool])(DT)
        if not P.any():
            continue

        F = np.column_stack((T, P, C))
        F = np.array(list(filter(lambda x: x[1], F)))
        F = np.delete(F, 1, 1)

        if time_classes is None:
            time_classes = F
        else:
            time_classes = np.vstack((time_classes, F))
    time_classes = sorted(time_classes, key=lambda x: x[0])
    time_classes = list(map(lambda tc: (tc[0], classes[tc[1]]), time_classes))
    return time_classes

def compute_presence_matrix(data_by_nickname, window_duration, as_probability=True):
    time_classes = compute_present_classes_by_timestamp(data_by_nickname)

    windows = []
    window, start_time = None, 0.

    for t, class_ in time_classes:
        if window is None:
            window, start_time = set([class_]), t
            continue

        duration = abs(t - start_time)
        if duration < window_duration:
            window.add(class_)
        else:
            windows.append(window)
            window, start_time = set([class_]), t

    classes = set(it.chain.from_iterable(windows))
    presence_matrix = { c : { c : 0 for c in classes } for c in classes }

    for window in windows:
        for c1, c2 in it.product(window, window):
            if c1 == c2:
                continue

            presence_matrix[c1].setdefault(c2, 0)
            presence_matrix[c2].setdefault(c1, 0)
            presence_matrix[c1][c2] += 1
            presence_matrix[c2][c1] += 1

    if as_probability:
        for nickname, adjacencies in presence_matrix.items():
            total = sum(adjacencies.values())
            if total == 0:
                continue
            for other_nickname in adjacencies:
                adjacencies[other_nickname] /= total
    return presence_matrix

def compute_presence_matrix_from_history(history, window_duration, as_probability=True):
    data_by_nickname = dict(map(lambda n_tm: (n_tm[0], list(map(lambda x: x[0], n_tm[1]))), history))
    return compute_presence_matrix(data_by_nickname, window_duration, as_probability)

if __name__ == '__main__':
    import sys
    import csv

    from models import get_history

    window_duration = 5 * 60

    if len(sys.argv) > 2:
        try:
            window_duration = int(sys.argv[1])
            if window_duration <= 0:
                raise ValueError
        except ValueError:
            print('window duration should be a positive integer', file=sys.stderr)
            sys.exit(1)

    history = get_history()
    presence_matrix = compute_presence_matrix_from_history(history, window_duration)

    import pprint; pprint.pprint(presence_matrix)
