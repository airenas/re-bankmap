import argparse
import sys

from egs.cmp_matrix.local.similarities import param_names, sim_imp
from src.utils.logger import logger


def main(argv):
    parser = argparse.ArgumentParser(description="Show criteria weights",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    args = parser.parse_args(args=argv)

    logger.info("Starting")

    pn = param_names()
    pv = sim_imp
    pt = [(p, pv[i]) for i, p in enumerate(pn)]
    pt.sort(key=lambda p: p[1], reverse=True)
    for p in pt:
        logger.info(
            "%s\t%.4f" % (p[0], p[1]))
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
