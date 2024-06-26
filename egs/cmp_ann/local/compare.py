import argparse
import sys

import pandas as pd
from sklearn.metrics import accuracy_score

from bankmap.data import e_str, LType
from bankmap.logger import logger


def first_word(l1):
    w1 = l1.split("\t")
    return w1[0].strip()


def show_no_rejected(y_true, y_pred, name, filter):
    y_true_nr = [x for i, x in enumerate(y_true) if y_pred[i] != 'rejected' and filter(y_true[i])]
    y_pred_nr = [x for i, x in enumerate(y_pred) if y_pred[i] != 'rejected' and filter(y_true[i])]

    rejected = sum([1 for i, x in enumerate(y_pred) if x == 'rejected' and filter(y_true[i])])
    all = sum([1 for i, x in enumerate(y_pred) if filter(y_true[i])])

    if len(y_true_nr) > 0:
        logger.info("{}: {:.3f} ({}/{})\trejected: {:.2f} {}/{}".format(name, accuracy_score(y_true_nr, y_pred_nr),
                                                                        sum([1 for i, x in enumerate(y_true_nr) if
                                                                             y_pred_nr[i] != x]),
                                                                        len(y_true_nr),
                                                                        rejected / all, rejected, all))
    else:
        logger.info("{}: {:.3f} ({}/{})\trejected: {}/{}".format(name, 0,
                                                                 sum([1 for i, x in enumerate(y_true_nr) if
                                                                      y_pred_nr[i] != x]),
                                                                 len(y_true_nr),
                                                                 sum([1 for i, x in enumerate(y_pred) if
                                                                      x == 'rejected' and filter(y_true[i])]),
                                                                 sum([1 for i, x in enumerate(y_pred) if
                                                                      filter(y_true[i])])
                                                                 ))


def cmp_arr(ya, pa):
    a = len(ya)
    ly = len(ya)
    lp = len(pa)
    for p in pa:
        if p in ya:
            ly -= 1
            lp -= 1
    return a, min(ly, lp), max(0, lp - ly), max(0, ly - lp)


def main(argv):
    parser = argparse.ArgumentParser(description="Compares two files",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--f1", nargs='?', required=True, help="File 1")
    parser.add_argument("--f2", nargs='?', required=True, help="File 2")
    parser.add_argument("--out", nargs='?', required=True, help="Output File")
    parser.add_argument("--skip", nargs='?', default=0, type=int, help="Skip [n] first items in comparison")
    parser.add_argument("--limit", nargs='?', default=0, type=float, help="Limit when to reject making decision")
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    logger.info("File 1: {}".format(args.f1))
    logger.info("File 2: {}".format(args.f2))
    with open(args.f2, 'r') as f2:
        y_pred_l = [line.strip() for line in f2]
    logger.info("loaded predicted {} rows".format(len(y_pred_l)))

    entries = pd.read_csv(args.f1, sep=',')
    logger.info("loaded entries {} rows".format(len(entries)))
    logger.debug("Headers: {}".format(list(entries)))
    y_true = entries["RecAccount"].values.tolist()
    y_rec_type = [e_str(v) for v in entries["RecType"].values.tolist()]

    y_true = ["%s:%s" % (y_rec_type[i], v) for i, v in enumerate(y_true)]
    y_true_docs = entries["RecDocs"].values.tolist()
    y_true_docs = [e_str(x) for x in y_true_docs]

    skip = args.skip
    y_true = y_true[skip:len(y_pred_l)]
    y_true_docs = y_true_docs[skip:len(y_pred_l)]
    y_pred = [y.split('\t')[0] for y in y_pred_l[skip:]]
    y_pred_docs = [y.split('\t')[1] for y in y_pred_l[skip:]]
    y_pred_v = [float(y.split('\t')[3]) for y in y_pred_l[skip:]]

    y_pred_reject = [x if y_pred_v[i] > args.limit else 'rejected' for i, x in enumerate(y_pred)]

    with open(args.out, 'w') as f:
        for i, y in enumerate(y_true):
            ir = i + skip
            v = y_pred_reject[i]
            val = y_pred_v[i]
            if v == y and val > args.limit:
                print("{}\t{}\t{}".format(ir, y, '' if y_rec_type[i] else 'empty'), file=f)
            else:
                print("{}\t{}\t{}\t{} <--diff-->\t{}\t{}".format(ir, y, v, '' if y_rec_type[i] else 'empty',
                                                                 [], val), file=f)

    y_true_n = [x for i, x in enumerate(y_true) if y_rec_type[i] != '']
    y_pred_n = [x for i, x in enumerate(y_pred) if y_rec_type[i] != '']

    logger.info("Acc all            : {:.3f} ({}/{})".format(accuracy_score(y_true_n, y_pred_n),
                                                             sum([1 for i, x in enumerate(y_true_n) if
                                                                  y_pred_n[i] != x]),
                                                             len(y_true_n)))
    y_pred_nreject = [x for i, x in enumerate(y_pred_reject) if y_rec_type[i] != '']

    show_no_rejected(y_true_n, y_pred_nreject, 'Acc not rejected   ', lambda p: True)
    show_no_rejected(y_true_n, y_pred_nreject, 'Acc BA             ', lambda p: p.startswith(LType.BA.to_s()))
    show_no_rejected(y_true_n, y_pred_nreject, 'Acc GL             ', lambda p: p.startswith(LType.GL.to_s()))
    show_no_rejected(y_true_n, y_pred_nreject, 'Acc Customer       ', lambda p: p.startswith(LType.CUST.to_s()))
    show_no_rejected(y_true_n, y_pred_nreject, 'Acc Vendor         ', lambda p: p.startswith(LType.VEND.to_s()))

    logger.info("Docs ...")
    rda, rds, rdi, rdd, rs, ny = 0, 0, 0, 0, 0, 0
    with open(args.out + '.docs', 'w') as f:
        for i, y in enumerate(y_true_docs):
            if not y:
                ny += 1
                continue
            ir = i + skip
            pa = y_pred_docs[i].split(";")
            ya = y.split(";")
            val = y_pred_v[i]
            se, ie, de, r = 0, 0, 0, ""
            if val > args.limit:
                a, se, ie, de = cmp_arr(ya, pa)
                rda, rds, rdi, rdd = rda + a, rds + se, rdi + ie, rdd + de
            else:
                r = "rejected"
                rs += len(ya)
            if (se + ie + de) == 0 and val > args.limit:
                print("{}\t{}".format(ir, y), file=f)
            else:
                print("{}\t{} {}<--diff-->\t{}".format(ir, y, r, y_pred_docs[i]), file=f)

    if rda > 0:
        logger.info(
            "Acc all {:.3f} ({}/{}) s:{}, i:{}, d:{}\t(rejected {}, no doc: {})".format(1 - ((rds + rdd + rdi) / rda),
                                                                                        (rds + rdd + rdi), rda, rds,
                                                                                        rdi, rdd, rs, ny))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
