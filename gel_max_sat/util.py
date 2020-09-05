def print_gel_max_sat_problem(kb, weights, result):
    print_header()
    problem = digest_problem(kb, weights)
    print_problem(problem)
    print_line()
    print_solution(problem, result)
    print_footer()
    return result


def print_line():
    print('-' * 60)


def print_header():
    print()
    print('-' * 20, 'GEL MAXSAT PROBLEM', '-' * 20)
    print('  i \t\t w(Ax_i) \t\t Ax_i')
    print_line()


def print_problem(problem):
    real_id = {}
    for i, (pbox_id, weight, axiom) in enumerate(problem):
        print('{:3}\t\t{}\t\t{}'.format(i, weight, axiom))
        real_id[pbox_id] = i


def name(kb, obj):
    if obj == kb.graph.top:
        return '⊤'

    if obj == kb.graph.bot:
        return '⊥'

    if kb.is_existential(obj):
        return f'∃{name(kb, obj.role_iri)}.{name(kb, obj.concept_iri)}'

    if kb.is_individual(obj):
        return '{' + name(kb, obj.iri) + '}'

    if not isinstance(obj, str):
        return name(kb, obj.iri)

    if '#' not in str(obj):
        return str(obj)

    return ''.join(obj.split('#')[1:])


def str_axiom(kb, sub_concept, role, sup_concept):
    s = f'{name(kb, sub_concept)} ⊑ '
    if role != kb.graph.is_a:
        s += f'∃{name(kb, role)}.'
    s += name(kb, sup_concept)
    return s


def is_real_axiom(kb, sub_concept, sup_arrow):
    is_init = kb.graph.init in [sub_concept, sup_arrow.concept]
    return not(is_init or sup_arrow.is_derivated)


def str_weight(pbox_id, weights):
    return '     ∞' if pbox_id < 0 else '{:+5.3f}'.format(weights[pbox_id])


def digest_problem(kb, weights):
    problem = []
    for concept in kb.concepts():
        for sup_arrow in concept.sup_arrows:
            sup_concept = sup_arrow.concept
            role = sup_arrow.role
            pbox_id = sup_arrow.pbox_id
            if is_real_axiom(kb, concept, sup_arrow):
                a = str_axiom(kb, concept, role, sup_concept)
                w = str_weight(pbox_id, weights)
                problem += [(pbox_id, w, a)]
    return problem


def print_solution(problem, result):
    print(f' HAS SOLUTION: {result["success"]}')

    if result['success']:
        excluded_ids = result['prob_axiom_indexes']
        excluded_axioms = []

        print('\n SOLUTION:')
        for pbox_id, _, axiom in problem:
            if pbox_id in excluded_ids:
                excluded_axioms += [axiom]
            else:
                print(f'\t{axiom}')

        print('\n EXCLUDED:')
        for axiom in excluded_axioms:
            print(f'\t{axiom}')


def print_footer():
    print_line()
    print('\n')
