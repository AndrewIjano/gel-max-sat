import sys
import gel_max_sat
from gel_max_sat import KnowledgeBase

def get_obj_str(obj):
    return obj.iri.split('#')[-1:][0]

def get_axiom_str(axiom):
    sub, sup, role = map(get_obj_str, axiom)
    return f'{sub} {role} {sup}'


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: python3 gel_max_sat.py <inputfile> [--trace]')
    else:
        filename = sys.argv[1]
        kb = KnowledgeBase.from_file(filename)
        weights = [1, 2, 3]
        result = gel_max_sat.solve(kb, weights)

        print(result)