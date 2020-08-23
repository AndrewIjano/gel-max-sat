import time
import numpy as np
import pandas as pd
import gel_max_sat
import argparse

IS_VERBOSE = False


def main():
    parser = init_argparse()
    args = parser.parse_args()

    global IS_VERBOSE
    IS_VERBOSE = args.verbose

    axioms_range = range(args.axioms_range_min,
                         args.axioms_range_max, args.axioms_range_step)

    data_set = run_experiments(
        axioms_range,
        args.concepts_count,
        args.prob_axioms_count,
        test_count=args.test_count,
        roles_count=args.roles_count
    )

    data_frame = create_data_frame(data_set)
    export_data_frame(data_frame, vars(args).values())


def init_argparse():
    parser = argparse.ArgumentParser(
        usage='%(prog)s [options]',
        description='Run experiments for GEL-MaxSAT algorithm.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument('-m', '--axioms-range-min', nargs='?',
                        default=11, type=int, help='minimum number of axioms tested')

    parser.add_argument('-M', '--axioms-range-max', nargs='?',
                        default=200, type=int, help='maximum number of axioms tested')

    parser.add_argument('-s', '--axioms-range-step', nargs='?',
                        default=1, type=int, help='step between each number of axioms tested in the range')

    parser.add_argument('-n', '--concepts-count', nargs='?',
                        default=60, type=int, help='number of concepts tested')

    parser.add_argument('-p', '--prob-axioms-count', nargs='?', default=10,
                        type=int, help='number of probabilistic axioms tested')

    parser.add_argument('-t', '--test-count', nargs='?', default=100,
                        type=int, help='number of tests for each axiom number')

    parser.add_argument('-r', '--roles-count', nargs='?', default=3,
                        type=int, help='number of roles tested')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='print the progress of the experiments')

    return parser


def print_verbose(*args, **kwargs):
    if IS_VERBOSE:
        print(*args, **kwargs)


def run_experiments(axioms_range, *args, **kwargs):
    data_set = []
    print_verbose('axioms |  time ')
    print_verbose('----------------')
    for axioms_count in axioms_range:
        print_verbose(end='  {:3}  | '.format(axioms_count))
        experiment = (axioms_count, *args)
        # print('>>>', experiment)
        data, exec_time = run_experiment(*experiment, **kwargs)
        data_set += [data]
        print_verbose('{:.5f}'.format(exec_time))
        # print(data)
    return data_set


def track_time(function):
    def wrap(*args, **kwargs):
        start = time.time()
        result = function(*args, **kwargs)
        end = time.time()
        return result, end - start
    return wrap


@track_time
def run_experiment(*args, **kwargs):
    (sat_mean, time_mean), (sat_std,
                            time_std) = test_gel_max_sat_satisfatibility(*args, **kwargs)
    axioms_count, concepts_count, prob_axioms_count = args
    return (concepts_count,
            axioms_count / concepts_count,
            prob_axioms_count,
            sat_mean,
            time_mean,
            sat_std,
            time_std)


def test_gel_max_sat_satisfatibility(axioms_count,
                                     concepts_count,
                                     prob_axioms_count,
                                     *args,
                                     test_count,
                                     **kwargs):

    def random_knowledge_bases():
        for _ in range(test_count):
            yield gel_max_sat.KnowledgeBase.random(
                concepts_count,
                axioms_count,
                prob_axioms_count,
                *(kwargs.values()))

    def random_weights():
        for _ in range(test_count):
            yield np.random.uniform(size=prob_axioms_count)

    sat_and_time_results = np.empty((test_count, 2))
    random_samples = zip(random_knowledge_bases(), random_weights())
    for idx, (kb, weights) in enumerate(random_samples):
        sat, time = gel_max_sat_is_satisfiable(kb, weights)
        sat_and_time_results[idx, 0] = sat
        sat_and_time_results[idx, 1] = time

    return np.mean(sat_and_time_results, axis=0), np.std(sat_and_time_results, axis=0)


@track_time
def gel_max_sat_is_satisfiable(knowledge_base, weights):
    return gel_max_sat.is_satisfiable(knowledge_base, weights)


def create_data_frame(data_set):
    return pd.DataFrame(
        data=data_set,
        columns=[
            'Concepts count',
            'Axioms count',
            'Uncertain axioms count',
            'SAT proportion mean',
            'Time mean',
            'SAT proportion std',
            'Time std',
            ])


def export_data_frame(data_frame, arg_values):
    filename = 'data/experiments/'
    filename += 'm{}-M{}-s{}-n{}-p{}-t{}-r{}'
    filename += '.csv'
    filename = filename.format(*arg_values)
    data_frame.to_csv(filename, index=False)


if __name__ == '__main__':
    main()
