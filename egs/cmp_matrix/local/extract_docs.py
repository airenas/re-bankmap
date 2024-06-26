import argparse
import sys

from bankmap.loaders.entries import load_docs_map
from bankmap.logger import logger
from bankmap.utils.utils import json_str


def main(argv):
    parser = argparse.ArgumentParser(description="Extracts external doc -> internal docs data",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", help="Customers applications file")
    parser.add_argument("--name", help="Internal ID field name")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

    res = load_docs_map(args.input, args.name)
    for k, v in res.items():
        out_v = {"ext_id": k, "doc_ids": ";".join(v[0]), "map": v[1]}
        print(json_str(out_v), file=sys.stdout)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
