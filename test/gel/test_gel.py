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
