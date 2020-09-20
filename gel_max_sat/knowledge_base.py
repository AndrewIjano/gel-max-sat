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

    @classmethod
    def from_file(cls, file):
        onto, graph = owl.parser.parse(file)
        graph.complete()

        kb = cls(graph)
        kb.onto = onto
        return kb

    @classmethod
    def random(cls, concepts_count=20,
               axioms_count=80,
               uncertain_axioms_count=10,
               roles_count=2):
        return cls(gel.Graph.random(concepts_count,
                                    axioms_count,
                                    uncertain_axioms_count,
                                    roles_count))
