import argparse
import random
import sys

import pandas as pd
from faker import Faker

from bankmap.logger import logger


def main(argv):
    parser = argparse.ArgumentParser(description="Anonymize file",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--f", nargs='?', required=True, help="File")
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    logger.info("File: {}".format(args.f))
    entries = pd.read_csv(args.f, sep=',')
    faker = Faker(locale="lt")

    def name(row):
        if bool(random.getrandbits(1)):
            return faker.name()
        return faker.company()

    def iban(row):
        return faker.iban()

    entries['Description'] = entries.apply(name, axis=1)
    entries['IBAN'] = entries.apply(iban, axis=1)

    entries.to_csv(sys.stdout, index=False)

    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
