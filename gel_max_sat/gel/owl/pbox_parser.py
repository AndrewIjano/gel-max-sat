import owlready2 as owl

PBOX_ID_HEADER = '#!pbox-id'


def get_id(owl_sub_concept, owl_sup_concept):
    if is_existential(owl_sub_concept):
        return -1

    comments = get_comments(owl_sub_concept, owl_sup_concept)
    for comment in comments:
        tokens = comment.split()
        if len(tokens) > 1 and tokens[0] == PBOX_ID_HEADER:
            return int(tokens[1])
    return -1


def is_existential(owl_concept):
    return isinstance(owl_concept, owl.class_construct.Restriction)


def get_comments(owl_sub_concept, owl_sup_concept):
    owl_is_a = owl.rdfs_subclassof
    return owl.comment[owl_sub_concept, owl_is_a, owl_sup_concept]
