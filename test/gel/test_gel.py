import pytest
from gel_max_sat import gel


@pytest.fixture
def simple_graph():
    graph = gel.Graph('bot', 'top')
    graph.add_concept(gel.Concept('C'))
    graph.add_concept(gel.IndividualConcept('a'))
    graph.add_role(gel.Role('r'))

    graph.add_concept(gel.ExistentialConcept('r', 'C'))
    graph.add_axiom('a', 'C', graph.is_a.iri)
    graph.complete()
    return graph


@pytest.fixture
def init_bot_graph():
    graph = gel.Graph('bot', 'top')
    graph.add_concept(gel.Concept('C'))
    graph.add_concept(gel.IndividualConcept('a'))
    graph.add_role(gel.Role('r'))
    graph.add_axiom('a', 'C', graph.is_a.iri)
    graph.add_axiom('C', 'bot', graph.is_a.iri)
    graph.complete()
    return graph


@pytest.fixture
def three_concept_graph():
    graph = gel.Graph('bot', 'top')
    graph.add_concept(gel.Concept('C'))
    graph.add_concept(gel.Concept('C_prime'))
    graph.add_concept(gel.Concept('D'))
    graph.add_role(gel.Role('i'))
    return graph


@pytest.fixture
def graph_pre_role_inclusion():
    graph = gel.Graph('bot', 'top')
    graph.add_concept(gel.Concept('C'))
    graph.add_concept(gel.Concept('D'))

    graph.add_role(gel.Role('i'))
    graph.add_role(gel.Role('j'))
    return graph


@pytest.fixture
def graph_pre_chained_role_inclusion():
    graph = gel.Graph('bot', 'top')
    graph.add_concept(gel.Concept('C'))
    graph.add_concept(gel.Concept('D_prime'))
    graph.add_concept(gel.Concept('D'))

    graph.add_role(gel.Role('i'))
    graph.add_role(gel.Role('j'))
    graph.add_role(gel.Role('k'))
    return graph


def test_graph_has_no_path_init_to_bot(simple_graph):
    assert not simple_graph.has_path_init_to_bot


def test_graph_has_path_init_to_bot(init_bot_graph):
    assert init_bot_graph.has_path_init_to_bot


def test_graph_concepts(simple_graph):
    expected_iris = [
        'init',
        'bot',
        'top',
        'C',
        'a',
        'r.C'
    ]

    expected_concepts = [
        simple_graph.get_concept(iri)
        for iri in expected_iris
    ]

    assert isinstance(simple_graph.concepts, list)
    assert simple_graph.concepts == expected_concepts


def test_graph_individuals(simple_graph):
    expected_iris = [
        'a'
    ]

    expected_individuals = [
        simple_graph.get_concept(iri)
        for iri in expected_iris
    ]

    assert isinstance(simple_graph.individuals, list)
    assert simple_graph.individuals == expected_individuals


def test_graph_roles(simple_graph):
    expected_iris = [
        'is a',
        'r'
    ]

    expected_roles = [
        simple_graph.get_role(iri)
        for iri in expected_iris
    ]

    assert isinstance(simple_graph.roles, list)
    assert simple_graph.roles == expected_roles


def test_graph_link_init(simple_graph):
    init = simple_graph.init
    concept_iris = ['top', 'a', 'C']
    concepts = [
        simple_graph.get_concept(iri)
        for iri in concept_iris
    ]

    assert concepts[0] in init.is_a()
    assert concepts[1] in init.is_a()
    assert concepts[2] not in init.is_a()


def test_graph_link_existential_concept(simple_graph):
    is_axiom_added = simple_graph.add_axiom('r.C', 'C', 'r',
                                            is_immutable=True)
    assert not is_axiom_added


def test_graph_add_axiom():
    graph = gel.Graph('bot', 'top')
    graph.add_concept(gel.Concept('C'))
    graph.add_concept(gel.Concept('D'))
    assert graph.add_axiom('C', 'D', graph.is_a)
    assert not graph.add_axiom('C', 'D', graph.is_a)


def test_graph_fix_existential_head_axiom(simple_graph):
    concept_D = gel.Concept('D')
    simple_graph.add_concept(concept_D)
    existential_concept = simple_graph.get_concept('r.C')
    assert existential_concept not in concept_D.is_a()
    simple_graph.add_axiom('D', 'C', 'r')
    assert existential_concept in concept_D.is_a()


def test_graph_add_pbox_axiom():
    graph = gel.Graph('bot', 'top')
    assert graph.pbox_axioms == {}

    graph.add_concept(gel.Concept('C'))
    graph.add_concept(gel.Concept('D'))
    graph.add_axiom('C', 'D', graph.is_a, pbox_id=0)

    expected_axiom = (
        graph.get_concept('C'),
        graph.get_concept('D'),
        graph.is_a
    )

    assert graph.pbox_axioms == {0: expected_axiom}


def test_graph_completion_rule_1_isa_first(three_concept_graph):
    # test "C ---> C' -i-> D" derivation
    graph = three_concept_graph
    graph.add_axiom('C', 'C_prime', graph.is_a)

    arrow = gel.Arrow(
        graph.get_concept('D'),
        graph.get_role('i'),
        is_derivated=True
    )

    concept_c = graph.get_concept('C')
    assert not concept_c.has_arrow(arrow)
    graph.add_axiom('C_prime', 'D', 'i')
    assert concept_c.has_arrow(arrow)


def test_graph_completion_rule_1_role_first(three_concept_graph):
    # test "C ---> C' -i-> D" derivation
    graph = three_concept_graph
    graph.add_axiom('C_prime', 'D', 'i')

    arrow = gel.Arrow(
        graph.get_concept('D'),
        graph.get_role('i'),
        is_derivated=True
    )

    concept_c = graph.get_concept('C')
    assert not concept_c.has_arrow(arrow)
    graph.add_axiom('C', 'C_prime', graph.is_a)
    assert concept_c.has_arrow(arrow)


def test_graph_completion_rule_2_isa_first(three_concept_graph):
    # test "C -i-> C' ---> D" derivation
    graph = three_concept_graph
    graph.add_axiom('C_prime', 'D', graph.is_a)

    arrow = gel.Arrow(
        graph.get_concept('D'),
        graph.get_role('i'),
        is_derivated=True
    )

    concept_c = graph.get_concept('C')
    assert not concept_c.has_arrow(arrow)
    graph.add_axiom('C', 'C_prime', 'i')
    assert concept_c.has_arrow(arrow)


def test_graph_completion_rule_2_role_first(three_concept_graph):
    # test "C -i-> C' ---> D" derivation
    graph = three_concept_graph
    graph.add_axiom('C', 'C_prime', 'i')

    arrow = gel.Arrow(
        graph.get_concept('D'),
        graph.get_role('i'),
        is_derivated=True
    )

    concept_c = graph.get_concept('C')
    assert not concept_c.has_arrow(arrow)
    graph.add_axiom('C_prime', 'D', graph.is_a)
    assert concept_c.has_arrow(arrow)


def test_graph_completion_rule_3(three_concept_graph):
    graph = three_concept_graph
    graph.add_concept(gel.ExistentialConcept('i', 'D'))

    arrow = gel.Arrow(
        graph.get_concept('i.D'),
        graph.is_a,
        is_derivated=True
    )

    concept_c = graph.get_concept('C')
    assert not concept_c.has_arrow(arrow)
    graph.add_axiom('C', 'D', 'i')
    assert concept_c.has_arrow(arrow)


def test_graph_completion_rule_3_axiom_first(three_concept_graph):
    graph = three_concept_graph
    graph.add_axiom('C', 'D', 'i')

    graph.add_concept(gel.ExistentialConcept('i', 'D'))

    arrow = gel.Arrow(
        graph.get_concept('i.D'),
        graph.is_a,
        is_derivated=True
    )

    # TODO:solve this problem 
    concept_c = graph.get_concept('C')
    assert concept_c.has_arrow(arrow)


def test_graph_completion_rule_4_bot_first(three_concept_graph):
    graph = three_concept_graph
    graph.add_axiom('D', 'bot', graph.is_a)

    arrow = gel.Arrow(
        graph.get_concept('D'),
        graph.is_a,
        is_derivated=True
    )

    concept_c = graph.get_concept('C')
    assert not concept_c.has_arrow(arrow)
    assert not concept_c.is_empty()
    graph.add_axiom('C', 'D', 'i')
    assert concept_c.has_arrow(arrow)
    assert concept_c.is_empty()


def test_graph_completion_rule_4_role_first(three_concept_graph):
    graph = three_concept_graph
    graph.add_axiom('C', 'D', 'i')

    arrow = gel.Arrow(
        graph.get_concept('D'),
        graph.is_a,
        is_derivated=True
    )

    concept_c = graph.get_concept('C')
    assert not concept_c.has_arrow(arrow)
    assert not concept_c.is_empty()
    graph.add_axiom('D', 'bot', graph.is_a)
    assert concept_c.has_arrow(arrow)
    assert concept_c.is_empty()


def test_graph_completion_rule_4_bot_connected_far(three_concept_graph):
    graph = three_concept_graph
    graph.add_concept(gel.Concept('E'))
    graph.add_axiom('D', 'E', graph.is_a)

    graph.add_axiom('C', 'D', 'i')
    arrow = gel.Arrow(
        graph.get_concept('D'),
        graph.is_a,
        is_derivated=True
    )

    concept_c = graph.get_concept('C')
    assert not concept_c.has_arrow(arrow)
    assert not concept_c.is_empty()
    graph.add_axiom('E', 'bot', graph.is_a)
    assert concept_c.has_arrow(arrow)
    assert concept_c.is_empty()


def test_graph_completion_rule_6_role_first(graph_pre_role_inclusion):
    graph = graph_pre_role_inclusion
    graph.add_role_inclusion('i', 'j')

    arrow = gel.Arrow(
        graph.get_concept('D'),
        graph.get_role('j'),
        is_derivated=True
    )

    concept_c = graph.get_concept('C')
    assert not concept_c.has_arrow(arrow)
    graph.add_axiom('C', 'D', 'i')
    assert concept_c.has_arrow(arrow)


def test_graph_completion_rule_6_axiom_first(graph_pre_role_inclusion):
    graph = graph_pre_role_inclusion
    graph.add_axiom('C', 'D', 'i')

    arrow = gel.Arrow(
        graph.get_concept('D'),
        graph.get_role('j'),
        is_derivated=True
    )

    concept_c = graph.get_concept('C')
    assert not concept_c.has_arrow(arrow)
    graph.add_role_inclusion('i', 'j')
    assert concept_c.has_arrow(arrow)


def test_graph_completion_rule_7_axiom1_after(
        graph_pre_chained_role_inclusion):
    graph = graph_pre_chained_role_inclusion
    graph.add_chained_role_inclusion(('i', 'j'), 'k')
    graph.add_axiom('D_prime', 'D', 'j')

    arrow = gel.Arrow(
        graph.get_concept('D'),
        graph.get_role('k'),
        is_derivated=True
    )

    concept_c = graph.get_concept('C')
    assert not concept_c.has_arrow(arrow)
    graph.add_axiom('C', 'D_prime', 'i')
    assert concept_c.has_arrow(arrow)


def test_graph_completion_rule_7_axiom2_after(
        graph_pre_chained_role_inclusion):
    graph = graph_pre_chained_role_inclusion
    graph.add_chained_role_inclusion(('i', 'j'), 'k')
    graph.add_axiom('C', 'D_prime', 'i')

    arrow = gel.Arrow(
        graph.get_concept('D'),
        graph.get_role('k'),
        is_derivated=True
    )

    concept_c = graph.get_concept('C')
    assert not concept_c.has_arrow(arrow)
    graph.add_axiom('D_prime', 'D', 'j')
    assert concept_c.has_arrow(arrow)


def test_graph_completion_rule_7_role_after(
        graph_pre_chained_role_inclusion):
    graph = graph_pre_chained_role_inclusion
    graph.add_axiom('C', 'D_prime', 'i')
    graph.add_axiom('D_prime', 'D', 'j')

    arrow = gel.Arrow(
        graph.get_concept('D'),
        graph.get_role('k'),
        is_derivated=True
    )

    concept_c = graph.get_concept('C')
    assert not concept_c.has_arrow(arrow)
    graph.add_chained_role_inclusion(('i', 'j'), 'k')
    assert concept_c.has_arrow(arrow)
