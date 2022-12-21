import math
import re

import jellyfish
import nltk
import strsimpy

nltk.edit_distance("humpty", "dumpty")

split_regex = re.compile(" |,|;|:|-|\"|'|\(|\)|{|}|\.|\?|/|!|$|%|&|@|~|\+")


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
    if a_uniq == 0 or b_uniq == 0:
        return 0
    return 0.7 * sequence_uniqueness(set(a_tokens).intersection(b_tokens)) / (a_uniq * b_uniq) ** 0.5 \
           + 0.2 * jellyfish.jaro_winkler_similarity(al, bl) \
           + 0.1 * jellyfish.jaro_winkler_similarity(a, b)


def date_sim(due_date, date):
    if date is None or due_date is None:
        return 0
    diff = (due_date - date).days
    return 1 - math.tanh(abs(diff / 20))


def num_sim(val):
    return 1 - math.tanh(abs(val / 10))


def sf_dist(sf1, sf2):
    def isnum(x):
        return '0' <= x <= '9'

    a = strsimpy.WeightedLevenshtein()

    def deletion_cost(char, pos, l):
        if pos < 3 and not isnum(char):
            return 0.3
        if pos < 4 and char == '0':
            return 0.3
        if pos == (l - 1) and isnum(char):
            return 0.3
        if pos == (l - 2) and char == '-':
            return 0.3
        return 1.0

    a.deletion_cost_fn = deletion_cost

    def insertion_cost(char, pos):
        if pos < 3:
            return 0.3
        return 1.0

    a.insertion_cost_fn = insertion_cost

    def subs_cost(ch1, ch2, pos):
        if pos > 3 and isnum(ch1) and isnum(ch2):
            return .4
        return 1.0

    a.substitution_cost_fn = subs_cost
    return a.distance(sf1, sf2)


def contains_number(string):
    return any(char.isdigit() for char in string)


def sf_sim(sf1, txt):
    res, _ = sf_sim_out(sf1, txt)
    return res


def sf_sim_out(sf1: str, txt: str):
    sf1 = sf1.casefold()
    tl = drop_empty(split_regex.split(txt.casefold()))
    res, bt = 1, ""
    for t in tl:
        if contains_number(t):
            v = sf_dist(sf1, t)
            if v == 0:
                return 1, t
            if v < 1 and v < res:
                res = v
                bt = t
    return 1 - res, bt
