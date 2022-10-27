import re

import jellyfish

split_regex = re.compile(" |,|\"|'")


def freq(t):
    if t in ["uab", "ab"]:
        return 2
    return 1


def sequence_uniqueness(seq):
    return sum(1 / freq(t) ** 0.5 for t in seq)


def drop_empty(param):
    return list(filter(lambda s: s != "", param))


# from http://nadbordrozd.github.io/blog/2016/07/29/datamatching-part-3-match-scoring/
def name_sim(a, b):
    al = a.lower()
    bl = b.lower()
    a_tokens = drop_empty(split_regex.split(al))
    b_tokens = drop_empty(split_regex.split(bl))

    a_uniq = sequence_uniqueness(a_tokens)
    b_uniq = sequence_uniqueness(b_tokens)

    return 0.7 * sequence_uniqueness(set(a_tokens).intersection(b_tokens)) / (a_uniq * b_uniq) ** 0.5 \
           + 0.2 * jellyfish.jaro_winkler_similarity(al, bl) \
           + 0.1 * jellyfish.jaro_winkler_similarity(a, b)
