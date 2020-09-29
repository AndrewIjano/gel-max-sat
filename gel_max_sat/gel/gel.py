import random
from queue import Queue
from .concepts import (
    Concept,
    EmptyConcept,
    GeneralConcept,
    ExistentialConcept,
    IndividualConcept,
)
from .roles import Role, IsA
from .arrows import Arrow


class Axiom:
    def __init__(self, graph, sub_concept, sup_concept, role, pbox_id=-1, is_derivated=False):
        self.graph = graph
        self.sub_concept = graph.get_concept(sub_concept)
        self.sup_concept = graph.get_concept(sup_concept)
        self.role = graph.get_role(role)
        self.pbox_id = pbox_id
        self.is_derivated = is_derivated

    @property
    def arrow(self):
        return Arrow(self.sup_concept, self.role, self.pbox_id, self.is_derivated)

    @property
    def is_new(self):
        return not self.sub_concept.has_arrow(self.arrow)

    @property
    def is_uncertain(self):
        return self.pbox_id >= 0

    def fix_existential_head(self):
        existential_concept = ExistentialConcept(self.role.iri, self.sup_concept.iri)
        if self.graph.has_concept(existential_concept):
            self.sup_concept = self.graph.get_concept(existential_concept.iri)
            self.role = self.graph.is_a

    def add(self):
        self.sub_concept.add_arrow(self.arrow)
        self.role.add_axiom(self.sub_concept, self.sup_concept)


class Graph:
    def __init__(self, empty_concept_iri, general_concept_iri):
        self.init = Concept('init')
        self.bot = EmptyConcept(empty_concept_iri)
        self.top = GeneralConcept(general_concept_iri)

        self.is_a = IsA()

        self._concepts = {c.iri: c for c in [self.init, self.bot, self.top]}
        self._roles = {r.iri: r for r in [self.is_a]}

        self.role_inclusions = {}
        self.pbox_axioms = {}

        self.init.add_arrow(Arrow(self.top, self.is_a))

        self.derivation_queue = Queue()
        self.derivations = 0
        self.axioms_added = 0

    @property
    def has_path_init_to_bot(self):
        return self.init.is_empty()

    @property
    def concepts(self):
        return list(self._concepts.values())

    @property
    def existential_concepts(self):
        return [concept for concept in self.concepts
                if isinstance(concept, ExistentialConcept)]

    @property
    def individuals(self):
        return [concept for concept in self.concepts
                if isinstance(concept, IndividualConcept)]

    @property
    def roles(self):
        return list(self._roles.values())

    def add_concept(self, concept):
        self._concepts[concept.iri] = concept

        if isinstance(concept, IndividualConcept):
            self.init.add_arrow(Arrow(concept, self.is_a))

        if isinstance(concept, ExistentialConcept):
            self.fix_previous_existential_head_axioms(concept)
            self.link_existential_concept(concept)

    def has_concept(self, concept):
        return concept.iri in self._concepts

    def get_concept(self, concept):
        if isinstance(concept, Concept):
            return concept
        if concept not in self._concepts:
            raise ValueError(f'Concept missing: {concept}')
        return self._concepts[concept]

    def fix_previous_existential_head_axioms(self, existential_concept):
        role = self.get_role(existential_concept.role_iri)
        origin_concept = self.get_concept(existential_concept.concept_iri)

        def outdated_sub_concepts():
            for sub_concept, sup_concept in role.axioms:
                if sup_concept == origin_concept:
                    yield sub_concept

        def new_role_axioms():
            axioms = []
            for sub_concept, sup_concept in role.axioms:
                if sup_concept != origin_concept:
                    axioms += [(sub_concept, sup_concept)]
            return axioms

        for sub_concept in outdated_sub_concepts():
            arrow = Arrow(origin_concept, role)
            sub_concept.remove_arrow(arrow)
            self.add_axiom(sub_concept, existential_concept, self.is_a)

        role.axioms = new_role_axioms()

    def link_existential_concept(self, concept):
        # get ri
        role_iri = concept.role_iri
        # get Cj
        origin_concept_iri = concept.concept_iri
        # add '∃ri.Cj' ⊑ ∃ri.Cj
        self.add_axiom(
            concept,
            origin_concept_iri,
            role_iri,
            is_immutable=True)

    def add_role(self, role):
        self._roles[role.iri] = role

    def get_role(self, role):
        if isinstance(role, Role):
            return role
        if role not in self._roles:
            raise ValueError(f'Role missing: {role}')
        return self._roles[role]

    def add_chained_role_inclusion(self, sub_roles_iri, sup_role_iri):
        sub_role1 = self.get_role(sub_roles_iri[0])
        sub_role2 = self.get_role(sub_roles_iri[1])
        sup_role = self.get_role(sup_role_iri)

        sup_roles = self.role_inclusions.get(sub_roles_iri, [])
        sup_roles += [sup_role]
        self.role_inclusions[sub_roles_iri] = sup_roles
        self.check_new_derivations_from_chained_role_inclusions(
            sub_role1, sub_role2, sup_role)

    def check_new_derivations_from_chained_role_inclusions(
            self, sub_role1, sub_role2, sup_role):
        for c, d_prime in sub_role1.axioms:
            for d in d_prime.sup_concepts(sub_role2):
                self.derive_axiom(c, d, sup_role)

    def add_role_inclusion(self, sub_role_iri, sup_role_iri):
        sub_role = self.get_role(sub_role_iri)
        sup_role = self.get_role(sup_role_iri)

        sup_roles = self.role_inclusions.get(sub_role_iri, [])
        sup_roles += [sup_role]
        self.role_inclusions[sub_role_iri] = sup_roles
        self.check_new_derivations_from_role_inclusions(sub_role, sup_role)

    def check_new_derivations_from_role_inclusions(self, sub_role, sup_role):
        for sub_concept, sup_concept in sub_role.axioms:
            self.derive_axiom(sub_concept, sup_concept, sup_role)

    def add_random_axioms(self, axioms_count, is_uncertain=False):
        axioms = 0
        while axioms < axioms_count:
            pbox_id = axioms if is_uncertain else -1
            axioms += self.add_random_axiom(pbox_id=pbox_id)

    def add_random_axiom(self, pbox_id=-1):
        return self.add_axiom(
            random.choice(self.real_concepts).iri,
            random.choice(self.real_concepts).iri,
            random.choice(self.roles).iri,
            pbox_id=pbox_id
        )

    def derive_axiom(self, sub_concept, sup_concept, role):
        arrow = Arrow(sup_concept, role, -1, True)
        axiom = (sub_concept, sup_concept, role)
        if not sub_concept.has_arrow(arrow) and axiom not in self.derivation_queue.queue:
            self.derivation_queue.put(axiom)
            self.derivations += 1

    def derive_axioms(self):
        while not self.derivation_queue.empty():
            axiom = self.derivation_queue.get()
            self.add_axiom(*axiom, is_derivated=True)

    def add_axiom(self, sub_concept, sup_concept, role,
                  pbox_id=-1, is_derivated=False, is_immutable=False):

        axiom = Axiom(self, sub_concept, sup_concept, role, pbox_id, is_derivated)
        if not is_immutable:
            axiom.fix_existential_head()

        if not axiom.is_new:
            return False

        self.axioms_added += 1
        axiom.add()

        if axiom.is_uncertain:
            self.add_pbox_axiom(axiom)

        self.check_new_derivations_from_axioms(axiom)
        self.check_new_paths_to_bot(axiom)
        self.check_new_derivations_from_axioms_and_roles(axiom)
        return True

    def add_pbox_axiom(self, axiom):
        self.pbox_axioms[axiom.pbox_id] = (axiom.sub_concept, axiom.sup_concept, axiom.role)

    def check_new_derivations_from_axioms(self, axiom):
        if axiom.role == self.is_a:
            self.check_new_derivation_from_isa_axioms(axiom)
        else:
            self.check_new_derivation_from_role_axioms(axiom)

    def check_new_derivation_from_isa_axioms(self, axiom):
        for c, i in axiom.sub_concept.sub_concepts_with_roles(without=self.is_a):
            self.derive_axiom(c, axiom.sup_concept, i)

        for d, i in axiom.sup_concept.sup_concepts_with_roles(without=self.is_a):
            self.derive_axiom(axiom.sub_concept, d, i)

    def check_new_derivation_from_role_axioms(self, axiom):
        for c in axiom.sub_concept.sub_concepts(role=self.is_a):
            self.derive_axiom(c, axiom.sup_concept, axiom.role)

        for d in axiom.sup_concept.sup_concepts(role=self.is_a):
            self.derive_axiom(axiom.sub_concept, d, axiom.role)

    def check_new_paths_to_bot(self, axiom):
        if axiom.sup_concept.is_empty() and axiom.role != self.is_a:
            axiom.sub_concept._is_empty = True
            self.derive_axiom(axiom.sub_concept, axiom.sup_concept, self.is_a)

        if axiom.sup_concept.is_empty() and axiom.role == self.is_a:
            for c, _ in axiom.sub_concept.sup_concepts_with_roles(without=self.is_a):
                if c.is_empty():
                    self.derive_axiom(axiom.sub_concept, c, self.is_a)

    def check_new_derivations_from_axioms_and_roles(self, axiom):
        for sup_role in self.role_inclusions.get(axiom.role.iri, []):
            self.derive_axiom(axiom.sub_concept, axiom.sup_concept, sup_role)

        for d, j in axiom.sup_concept.sup_concepts_with_roles(without=self.is_a):
            for k in self.role_inclusions.get((axiom.role.iri, j.iri), []):
                self.derive_axiom(axiom.sub_concept, d, k)

        for c, j in axiom.sub_concept.sub_concepts_with_roles(without=self.is_a):
            for k in self.role_inclusions.get((j.iri, axiom.role.iri), []):
                self.derive_axiom(c, axiom.sup_concept, k)

    def check_equivalent_concepts(self):
        def is_reached_by_init(c, d):
            reached_by_init = list(self.init.sup_concepts_reached())
            return c in reached_by_init and d in reached_by_init

        for a in self.individuals:
            for c in a.sub_concepts_reach():
                for d in a.sub_concepts_reach():
                    if is_reached_by_init(c, d):
                        self.derive_axiom(c, d, self.is_a)

    def complete(self):
        while not self.derivation_queue.empty():
            self.derive_axioms()
            self.check_equivalent_concepts()
        print(f'({self.axioms_added}, {self.derivations})', end=' ')

    @classmethod
    def random(cls,
               concepts_count=20,
               axioms_count=80,
               uncertain_axioms_count=10,
               roles_count=2):

        graph = cls('bot', 'top')
        # add concepts
        for i in range(concepts_count):
            concept = Concept(i)
            graph.add_concept(concept)

        # add roles
        for i in range(roles_count):
            graph.add_role(Role(chr(ord('r') + i)))

        # add certain axioms randomly
        certain_axioms_count = max(0, axioms_count - uncertain_axioms_count)
        graph.real_concepts = [c for c in graph.concepts]
        graph.add_random_axioms(certain_axioms_count)

        # add uncertain axioms randomly
        graph.add_random_axioms(uncertain_axioms_count, is_uncertain=True)

        graph.complete()
        return graph
