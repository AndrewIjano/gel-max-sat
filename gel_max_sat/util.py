def print_gel_max_sat_problem(kb, weights, result):
    print_header()
    problem = digest_problem(kb, weights)
    print_problem(problem)
    print_line()
    print_solution(problem, result)
    print_footer()


URI_IS_A_CONCEPT = 'http://www.w3.org/2000/01/rdf-schema#subClassOf'
URI_IS_A_INDIVIDUAL = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'


def save_solution(kb, result, filename):
    ntriples = convert_solution_to_ntriples(kb, result)

    with open(filename, 'w+') as f:
        f.write(ntriples)


def convert_solution_to_ntriples(kb, result):
    def get_role_iri(role, sub_concept):
        if kb.is_isa(role) and kb.is_individual(sub_concept):
            return URI_IS_A_INDIVIDUAL
        if kb.is_isa(role):
            return URI_IS_A_CONCEPT
        return role.iri

    def get_concept_iri(concept):
        if kb.is_existential(concept):
            return concept.role_iri + '.' + name(kb, concept.concept_iri)
        return concept.iri

    def get_triple(sub_concept_iri, role_iri, sup_concept_iri):
        return f'<{sub_concept_iri}> <{role_iri}> <{sup_concept_iri}> .'

    ntriples = []
    for sub_concept in kb.concepts():
        for sup_arrow in sub_concept.sup_arrows:
            sup_concept = sup_arrow.concept
            role = sup_arrow.role

            role_iri = get_role_iri(role, sub_concept)
            sub_concept_iri = get_concept_iri(sub_concept)
            sup_concept_iri = get_concept_iri(sup_concept)

            pbox_id = sup_arrow.pbox_id

            excluded_ids = result['prob_axiom_indexes']
            if is_real_axiom(kb, sub_concept,
                             sup_arrow) and pbox_id not in excluded_ids:
                ntriples += [get_triple(sub_concept_iri,
                                        role_iri, sup_concept_iri)]
    return '\n'.join(ntriples)


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
            sup_concept = sup_arrow.concept
            role = sup_arrow.role
            pbox_id = sup_arrow.pbox_id
            if is_real_axiom(kb, concept, sup_arrow):
                a = str_axiom(kb, concept, role, sup_concept)
                w = str_weight(pbox_id, weights)
                problem += [(pbox_id, w, a)]
    return problem


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


def name(kb, obj):
    if obj == kb.graph.top:
        return '⊤'

    if obj == kb.graph.bot:
        return '⊥'

    if kb.is_existential(obj):
        return f'"∃{name(kb, obj.role_iri)}.{name(kb, obj.concept_iri)}"'

    if kb.is_individual(obj):
        return '{' + name(kb, obj.iri) + '}'

    if not isinstance(obj, str):
        return name(kb, obj.iri)

    if '#' not in str(obj):
        return str(obj)

    return ''.join(obj.split('#')[1:])


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
            else:
                print(f'\t{axiom}')

        print('\n EXCLUDED:')
        for axiom in excluded_axioms:
            print(f'\t{axiom}')


def print_footer():
    print_line()
    print()
