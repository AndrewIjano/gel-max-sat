import gel_max_sat
from gel_max_sat import KnowledgeBase, print_gel_max_sat_problem, save_solution
import argparse


def main():
    parser = init_argparse()
    args = parser.parse_args()
    filename = args.file[0]
    weights = args.weights

    kb = KnowledgeBase.from_file(filename)
    result = gel_max_sat.solve(kb, weights)

    if args.verbose:
        print_gel_max_sat_problem(kb, weights, result)
    else:
        print(has_solution(result))

    if has_solution(result):
        save_solution(kb, result, args.output)


def has_solution(result):
    return result['success']


def init_argparse():
    parser = argparse.ArgumentParser(
        description='Computes the GEL-MaxSAT algorithm in a weighted Graphic EL knowledge base.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
        'file', nargs=1, type=str,
        help='path of the OWL file with the Graphic EL ontology')

    parser.add_argument('-w', '--weights', nargs='*', type=int,
                        help='the finite weights of the knowledge base')

    parser.add_argument('-o', '--output', nargs='?', default='solution.nt',
                        type=str, help='path for the GEL-MaxSAT solution in N-Triples format')

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='prints the problem and solution')
    return parser


if __name__ == '__main__':
    main()
