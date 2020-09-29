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

# class Axiom:
#     def __init__(self, graph, sub_concept, sup_concept, role):
#         self.sub_concept = graph.get_concept(sub_concept)
#         self.sup_concept = graph.get_concept(sup_concept)
#         self.role = graph.get_role(role)
#

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
        if not sub_concept.has_arrow(arrow):
            axiom = (sub_concept, sup_concept, role)
            self.derivation_queue.put(axiom)
            self.derivations += 1

    def derive_axioms(self):
        while not self.derivation_queue.empty():
            axiom = self.derivation_queue.get()
            self.add_axiom(*axiom, is_derivated=True)

    def add_axiom(self, sub_concept, sup_concept, role,
                  pbox_id=-1, is_derivated=False, is_immutable=False):
        sub_concept = self.get_concept(sub_concept)
        sup_concept = self.get_concept(sup_concept)
        role = self.get_role(role)

        sup_concept, role = self.fix_existential_head_axiom(
            sup_concept, role, is_immutable)

        arrow = Arrow(sup_concept, role, pbox_id, is_derivated)
        if not sub_concept.has_arrow(arrow):
            sub_concept.add_arrow(arrow)

            role.add_axiom(sub_concept, sup_concept)
            axiom = (sub_concept, sup_concept, role)
            if pbox_id >= 0:
                self.add_pbox_axiom(pbox_id, axiom)

            self.check_new_derivations_from_axioms(axiom)
            self.check_new_paths_to_bot(axiom)
            self.check_new_derivations_from_axioms_and_roles(axiom)
            return True
        return False

    def fix_existential_head_axiom(self, sup_concept, role, is_immutable):
        existential_concept = ExistentialConcept(role.iri, sup_concept.iri)
        if not is_immutable and existential_concept.iri in self._concepts:
            return self.get_concept(existential_concept.iri), self.is_a
        return sup_concept, role

    def add_pbox_axiom(self, pbox_id, axiom):
        self.pbox_axioms[pbox_id] = axiom

    def check_new_derivations_from_axioms(self, axiom):
        _, _, role = axiom
        if role == self.is_a:
            self.check_new_derivation_from_isa_axioms(axiom)
        else:
            self.check_new_derivation_from_role_axioms(axiom)

    def check_new_derivation_from_isa_axioms(self, axiom):
        sub_concept, sup_concept, _ = axiom
        for c, i in sub_concept.sub_concepts_with_roles(without=self.is_a):
            self.derive_axiom(c, sup_concept, i)

        for d, i in sup_concept.sup_concepts_with_roles(without=self.is_a):
            self.derive_axiom(sub_concept, d, i)

    def check_new_derivation_from_role_axioms(self, axiom):
        sub_concept, sup_concept, role = axiom
        for c in sub_concept.sub_concepts(role=self.is_a):
            self.derive_axiom(c, sup_concept, role)

        for d in sup_concept.sup_concepts(role=self.is_a):
            self.derive_axiom(sub_concept, d, role)

    def check_new_paths_to_bot(self, axiom):
        sub_concept, sup_concept, role = axiom
        if sup_concept.is_empty() and role != self.is_a:
            sub_concept._is_empty = True
            self.derive_axiom(sub_concept, sup_concept, self.is_a)

        if sup_concept.is_empty() and role == self.is_a:
            for c, _ in sub_concept.sup_concepts_with_roles(without=self.is_a):
                if c.is_empty():
                    self.derive_axiom(sub_concept, c, self.is_a)

    def check_new_derivations_from_axioms_and_roles(self, axiom):
        sub_concept, sup_concept, role = axiom
        for sup_role in self.role_inclusions.get(role.iri, []):
            self.derive_axiom(sub_concept, sup_concept, sup_role)

        for d, j in sup_concept.sup_concepts_with_roles(without=self.is_a):
            for k in self.role_inclusions.get((role.iri, j.iri), []):
                self.derive_axiom(sub_concept, d, k)

        for c, j in sub_concept.sub_concepts_with_roles(without=self.is_a):
            for k in self.role_inclusions.get((j.iri, role.iri), []):
                self.derive_axiom(c, sup_concept, k)

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
        print(f'({self.derivations})', end=' ')

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
