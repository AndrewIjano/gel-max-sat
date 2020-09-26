from . import roles


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

    def __repr__(self):
        return f'Arrow({repr(self.concept)},'\
            + f' {repr(self.role)},'\
            + f' {self.pbox_id},'\
            + f' {self.is_derivated})'

    @property
    def name(self):
        is_isa = isinstance(self.role, roles.IsA)
        return '⊑ {}{}'.format(
            '' if is_isa else f'∃{self.role.name}.',
            self.concept.name
        )
