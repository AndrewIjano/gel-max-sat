from . import owl
from . import gel


class KnowledgeBase:
    def __init__(self, graph):
        self.graph = graph

    def init(self):
        return self.graph.init.iri

    def bottom(self):
        return self.graph.bot.iri

    def concepts(self):
        return self.graph.concepts.values()

    def is_existential(self, concept):
        return isinstance(concept, gel.ExistentialConcept)

    def is_individual(self, concept):
        return isinstance(concept, gel.IndividualConcept)

    @classmethod
    def from_file(cls, file):
        graph = owl.parser.parse(file)
        graph.complete()

        return cls(graph)

    @classmethod
    def random(cls, concepts_count=20,
               axioms_count=80,
               uncertain_axioms_count=10,
               roles_count=2):
        return cls(gel.Graph.random(concepts_count,
                                    axioms_count,
                                    uncertain_axioms_count,
                                    roles_count))