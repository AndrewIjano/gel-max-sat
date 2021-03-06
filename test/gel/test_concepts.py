import pytest
from gel_max_sat import gel


@pytest.fixture
def concept_with_arrows():
    concept_a = gel.Concept('a')
    concept_b = gel.Concept('b')
    role = gel.Role('r')
    arrow1 = gel.Arrow(concept_b, role)
    concept_a.add_arrow(arrow1)

    concept_c = gel.Concept('c')
    arrow2 = gel.Arrow(concept_c, role)
    concept_a.add_arrow(arrow2)

    return concept_a, [arrow1, arrow2]


def test_concept_arrow_addition(concept_with_arrows):
    concept, arrows = concept_with_arrows
    assert set(arrows) == concept.sup_arrows


def test_concept_same_arrow_addition(concept_with_arrows):
    concept, arrows = concept_with_arrows
    concept.add_arrow(arrows[0])
    assert len(concept.sup_arrows) == len(arrows)


def test_concept_has_arrow(concept_with_arrows):
    concept, arrows = concept_with_arrows
    assert concept.has_arrow(arrows[0])


def test_same_values_arrow_equal(concept_with_arrows):
    concept, arrows = concept_with_arrows
    arrow = arrows[0]
    arrow2 = gel.Arrow(arrow.concept, arrow.role)
    assert concept.has_arrow(arrow2)


def test_concept_has_name(concept_with_arrows):
    concept, _ = concept_with_arrows
    assert concept.name == 'a'
