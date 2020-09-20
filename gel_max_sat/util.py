URI_IS_A_CONCEPT = 'http://www.w3.org/2000/01/rdf-schema#subClassOf'
URI_IS_A_INDIVIDUAL = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'


def save_solution(kb, result, filename):
    ntriples = convert_solution_to_ntriples(kb, result)

    with open(filename, 'w+') as f:
        f.write(ntriples)


def convert_solution_to_ntriples(kb, result):
    def get_role_iri(role, sub_concept):
        if role.is_isa and sub_concept.is_individual:
            return URI_IS_A_INDIVIDUAL
        if role.is_isa:
            return URI_IS_A_CONCEPT
        return role.iri

    def get_triple(sub_concept_iri, role_iri, sup_concept_iri):
        return f'<{sub_concept_iri}> <{role_iri}> <{sup_concept_iri}> .'

    ntriples = []
    for sub_concept in kb.concepts():
        for sup_arrow in sub_concept.sup_arrows:
            sup_concept = sup_arrow.concept
            role = sup_arrow.role

            role_iri = get_role_iri(role, sub_concept)

            pbox_id = sup_arrow.pbox_id

            excluded_ids = result['prob_axiom_indexes']
            if is_real_axiom(kb, sub_concept,
                             sup_arrow) and pbox_id not in excluded_ids:
                ntriples += [get_triple(sub_concept.iri,
                                        role_iri, sup_concept.iri)]
    return '\n'.join(ntriples)


def print_gel_max_sat_problem(kb, weights, result):
    print_header()
    problem = digest_problem(kb, weights)
    print_problem(problem)
    print_line()
    print_solution(problem, result)
    print_footer()


def print_line():
    print('-' * 60)


def print_header():
    print()
    print('-' * 20, 'GEL MAXSAT PROBLEM', '-' * 20)
    print('  i \t\t w(Ax_i) \t\t Ax_i')
    print_line()


def digest_problem(kb, weights):
    problem = []
    for concept in kb.concepts():
        for sup_arrow in concept.sup_arrows:
            pbox_id = sup_arrow.pbox_id
            if is_real_axiom(kb, concept, sup_arrow):
                axiom = f'{concept.name} {sup_arrow.name}'
                weight = str_weight(pbox_id, weights)
                problem += [(pbox_id, weight, axiom)]
    return problem


def is_real_axiom(kb, sub_concept, sup_arrow):
    has_init = kb.graph.init in [sub_concept, sup_arrow.concept]
    return not(has_init or sup_arrow.is_derivated)


def str_weight(pbox_id, weights):
    return '     ∞' if pbox_id < 0 else '{:+5.3f}'.format(weights[pbox_id])


def print_problem(problem):
    real_id = {}
    for i, (pbox_id, weight, axiom) in enumerate(problem):
        print('{:3}\t\t{}\t\t{}'.format(i, weight, axiom))
        real_id[pbox_id] = i


def print_solution(problem, result):
    print(f' HAS SOLUTION: {result["success"]}')

    if result['success']:
        excluded_ids = result['prob_axiom_indexes']
        excluded_axioms = []

        print('\n SOLUTION:')
        for pbox_id, _, axiom in problem:
            if pbox_id in excluded_ids:
                excluded_axioms += [axiom]
                continue
            print(f'\t{axiom}')

        print('\n EXCLUDED:')
        for axiom in excluded_axioms:
            print(f'\t{axiom}')


def print_footer():
    print_line()
    print()
