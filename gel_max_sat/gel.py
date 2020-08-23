import random


class Concept:
    def __init__(self, iri):
        self.iri = iri
        self.sup_arrows = []
        self.sub_arrows = []
        self._is_empty = False
        self.reaches = {self}

    def has_arrow(self, arrow):
        return arrow in self.sup_arrows

    def add_arrow(self, sup_arrow):
        sup_concept = sup_arrow.concept
        sub_arrow = sup_arrow.copy_from(self)
        if not self.has_arrow(sup_arrow):
            self.sup_arrows += [sup_arrow]
            sup_concept.sub_arrows += [sub_arrow]

    def is_a(self):
        return (a.concept for a in self.sup_arrows
                if isinstance(a.role, IsA) and a.pbox_id < 0)

    def sup_concepts(self, role=None):
        return (a.concept for a in self.sup_arrows
                if role is not None and a.role == role)

    def sup_concepts_with_roles(self, without=None):
        return ((a.concept, a.role) for a in self.sup_arrows
                if a.role != without)

    def sub_concepts(self, role=None):
        return (a.concept for a in self.sub_arrows
                if role is not None and a.role == role)

    def sub_concepts_with_roles(self, without=None):
        return ((a.concept, a.role) for a in self.sub_arrows
                if a.role != without)

    def is_empty(self):
        visited = set()

        def _is_empty(concept):
            if concept._is_empty:
                return True
            visited.add(concept)
            reached = False
            for sup_concept in concept.is_a():
                if sup_concept not in visited:
                    reached = reached or _is_empty(sup_concept)
            concept._is_empty = reached
        return _is_empty(self)

    def sup_concepts_reached(self, role=None):
        visited = set()

        def _sup_concepts_reached(concept):
            visited.add(concept)
            yield concept
            for sup_concept in concept.sup_concepts(role=role):
                if sup_concept not in visited:
                    yield from _sup_concepts_reached(sup_concept)

        yield from _sup_concepts_reached(self)

    def sub_concepts_reach(self, role=None):
        visited = set()

        def _sub_concepts_reached(concept):
            visited.add(concept)
            yield concept
            for sub_concept in concept.sub_concepts(role=role):
                if sub_concept not in visited:
                    yield from _sub_concepts_reached(sub_concept)

        yield from _sub_concepts_reached(self)


class EmptyConcept(Concept):
    def __init__(self, iri):
        super().__init__(iri)
        self._is_empty = True


class IndividualConcept(Concept):
    def __init__(self, iri):
        super().__init__(iri)


class ExistentialConcept(Concept):
    def __init__(self, role_iri, concept_iri):
        self.concept_iri = concept_iri
        self.role_iri = role_iri
        super().__init__(f'{role_iri}.{concept_iri}')


class Arrow():
    def __init__(self, concept, role, pbox_id=-1, is_derivated=False):
        self.concept = concept
        self.role = role
        self.pbox_id = pbox_id
        self.is_derivated = is_derivated

    def copy_from(self, concept):
        return Arrow(concept, self.role, self.pbox_id, self.is_derivated)

    def __eq__(self, other):
        if not isinstance(other, Arrow):
            return NotImplemented

        return (self.concept == other.concept and
                self.role == other.role)


class Role():
    def __init__(self, iri):
        self.iri = iri
        self.axioms = []

    def add_axiom(self, sub_concept, sup_concept):
        self.axioms += [(sub_concept, sup_concept)]


class IsA(Role):
    def __init__(self):
        super().__init__('is a')


class ArtificialRole(Role):
    def __init__(self, dual_role_iri, concept_iri):
        self.dual_role_iri = dual_role_iri
        self.concept_iri = concept_iri
        super().__init__(f'{dual_role_iri}.{concept_iri}')


class Graph():
    def __init__(self, empty_concept_iri, general_concept_iri):
        self.init = Concept('init')
        self.bot = EmptyConcept(empty_concept_iri)
        self.top = Concept(general_concept_iri)

        self.is_a = IsA()

        self.concepts = {c.iri: c for c in [self.init, self.bot, self.top]}
        self.roles = {r.iri: r for r in [self.is_a]}
        self.role_inclusions = {}

        self.pbox_axioms = {}
        self.init.add_arrow(Arrow(self.top, self.is_a))

    def has_path_init_to_bot(self):
        return self.init.is_empty()

    def add_concept(self, concept):
        self.concepts[concept.iri] = concept

        if isinstance(concept, IndividualConcept):
            self.init.add_arrow(Arrow(concept, self.is_a))

        if isinstance(concept, ExistentialConcept):
            self.link_existential_concept(concept)

    def link_existential_concept(self, concept):
        # get ri
        role_iri = concept.role_iri
        # get Cj
        origin_concept_iri = concept.concept_iri
        # add '∃ri.Cj' ⊑ ∃ri.Cj
        self.add_axiom(concept, origin_concept_iri, role_iri)

    def get_concept(self, concept):
        if not isinstance(concept, Concept):
            return self.concepts[concept]
        return concept

    def get_concepts(self):
        return list(self.concepts.values())

    def add_role(self, role):
        self.roles[role.iri] = role

    def get_role(self, role):
        if not isinstance(role, Role):
            return self.roles[role]
        return role

    def get_roles(self):
        return list(self.roles.values())

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
        for c, d_prime in sub_role1.axioms():
            for d in d_prime.sup_concepts(sub_role2):
                self.add_axiom(c.iri, d.iri, sup_role.iri, is_derivated=True)

    def add_role_inclusion(self, sub_role_iri, sup_role_iri):
        sub_role = self.get_role(sub_role_iri)
        sup_role = self.get_role(sup_role_iri)

        sup_roles = self.role_inclusions.get(sub_role_iri, [])
        sup_roles += [sup_role]
        self.role_inclusions[sub_role_iri] = sup_roles
        self.check_new_derivations_from_role_inclusions(sub_role, sup_role)

    def check_new_derivations_from_role_inclusions(self, sub_role, sup_role):
        for c, d in sub_role.axioms():
            self.add_axiom(c, d, sup_role, is_derivated=True)

    def add_random_axioms(self, axioms_count, is_uncertain=False):
        axioms = 0
        while axioms < axioms_count:
            pbox_id = axioms if is_uncertain else -1
            axioms += self.add_random_axiom(pbox_id=pbox_id)

    def add_random_axiom(self, pbox_id=-1):
        roles = self.get_roles()

        return self.add_axiom(
            random.choice(self.real_concepts).iri,
            random.choice(self.real_concepts).iri,
            random.choice(roles).iri,
            pbox_id=pbox_id
        )

    def add_axiom(self, sub_concept, sup_concept, role,
                  pbox_id=-1, is_derivated=False):
        sub_concept = self.get_concept(sub_concept)
        sup_concept = self.get_concept(sup_concept)
        role = self.get_role(role)

        sup_concept, role = self.remove_existential_body(sup_concept, role)
        arrow = Arrow(sup_concept, role, pbox_id, is_derivated)
        if not sub_concept.has_arrow(arrow):
            sub_concept.add_arrow(arrow)

            axiom = (sub_concept, sup_concept, role)
            if pbox_id >= 0:
                self.add_pbox_axiom(pbox_id, axiom)

            self.check_new_derivations_from_axioms(axiom)
            self.check_new_paths_to_bot(axiom)
            self.check_new_derivations_from_axioms_and_roles(axiom)
            return True
        return False

    def remove_existential_body(self, sup_concept, role):
        existential_concept = ExistentialConcept(role.iri, sup_concept.iri)
        if existential_concept.iri in self.concepts:
            return self.get_concept(existential_concept.iri), self.is_a
        return sup_concept, role

    def add_pbox_axiom(self, pbox_id, axiom):
        self.pbox_axioms[pbox_id] = axiom

    def check_link_to_existential_concept(self, axiom):
        sub_concept, sup_concept, role = axiom
        existential_concept = ExistentialConcept(role.iri, sup_concept.iri)
        if existential_concept.iri in self.concepts:
            existential_concept = self.get_concept(existential_concept.iri)
            # TODO: check if is derivated and pbox_id implications
            self.add_axiom(sub_concept, existential_concept, self.is_a)

    def check_new_derivations_from_axioms(self, axiom):
        sub_concept, sup_concept, role = axiom
        if role == self.is_a:
            for c, i in sup_concept.sup_concepts_with_roles(without=self.is_a):
                self.add_axiom(sup_concept, c, i, is_derivated=True)
            return
        for c in sub_concept.sub_concepts(role=self.is_a):
            self.add_axiom(c, sub_concept, role, is_derivated=True)

    def check_new_paths_to_bot(self, axiom):
        sub_concept, sup_concept, role = axiom
        if sup_concept.is_empty() and role != self.is_a:
            sub_concept._is_empty = True
            is_a = self.is_a
            self.add_axiom(sub_concept, sup_concept, is_a, is_derivated=True)

    def check_new_derivations_from_axioms_and_roles(self, axiom):
        sub_concept, sup_concept, role = axiom
        for sup_role in self.role_inclusions.get(role.iri, []):
            self.add_axiom(sub_concept, sup_concept, role, is_derivated=True)

        for d, j in sup_concept.sub_concepts_with_roles(without=self.is_a):
            for k in self.role_inclusions.get((role.iri, j.iri), []):
                self.add_axiom(sub_concept, d, k, is_derivated=True)

    def existential_concepts(self):
        return (concept for concept in self.concepts.values()
                if isinstance(concept, ExistentialConcept))

    def individuals(self):
        return (concept for concept in self.concepts.values()
                if isinstance(concept, IndividualConcept))

    def complete(self):
        def concepts_connected_by_existential(ri_e):
            i = self.get_role(ri_e.role_iri)
            e = self.get_concept(ri_e.concept_iri)
            for c in e.sub_concepts(role=i):
                for d in ri_e.sup_concepts(role=self.is_a):
                    yield c, d

        def complete_rule_3():
            ok = False
            for ri_e in self.existential_concepts():
                for c, d in concepts_connected_by_existential(ri_e):
                    ok = ok or self.add_axiom(
                        c, d, self.is_a, is_derivated=True)
            return ok

        def is_reached_by_init(c, d):
            reached_by_init = self.init.sup_concepts_reached()
            return c in reached_by_init and d in reached_by_init

        def complete_rule_5():
            ok = False
            for a in self.individuals():
                for c in a.sub_concepts_reach():
                    for d in a.sub_concepts_reach():
                        if is_reached_by_init(c, d):
                            ok = ok or self.add_axiom(
                                c, d, self.is_a, is_derivated=True)
            return ok

        ok = False
        while not ok:
            ok = True
            ok = ok and not complete_rule_3()
            ok = ok and not complete_rule_5()

    @classmethod
    def random(cls,
               concepts_count=20,
               axioms_count=80,
               uncertain_axioms_count=10,
               roles_count=2):

        graph = cls('bot', 'top')

        def get_random_concept(iri):
            return Concept(iri)

        for i in range(concepts_count):
            concept = get_random_concept(str(i))
            graph.add_concept(concept)

        # add roles
        for i in range(roles_count):
            graph.add_role(Role(chr(ord('r') + i)))

        # add certain axioms randomly
        certain_axioms_count = max(0, axioms_count - uncertain_axioms_count)
        graph.real_concepts = [c for c in graph.get_concepts()]
        graph.add_random_axioms(certain_axioms_count)

        # add uncertain axioms randomly
        graph.add_random_axioms(uncertain_axioms_count, is_uncertain=True)

        graph.complete()
        return graph
