import argparse
import sys

import pandas as pd

from bankmap.data import to_date
from bankmap.logger import logger


class logData:
    def __init__(self, data):
        strs = data.get("message", "").split(":")
        self.company = strs[1]
        self.entries = strs[2]
        self.lines = strs[3]
        self.recommended = strs[4]
        self.trained = int(strs[6]) if len(strs) > 6 and strs[6] != "" else 0
        self.trained_date = to_date(strs[7]).strftime("%Y%m%d") if len(strs) > 7 and strs[7] != "" else ""
        self.date = to_date(data.get("timestamp [UTC]", "no date")).strftime("%Y%m%d")
        self.time = to_date(data.get("timestamp [UTC]", "no date")).strftime("%H:%M:%S")

    def to_s(self):
        return "{}\t{}\t{}\t{}\t{}\t{}".format(self.date, self.company, self.trained, self.entries, self.lines,
                                               self.recommended)


def main(argv):
    parser = argparse.ArgumentParser(description="Parses logs file",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file of logs")
    parser.add_argument("--output", nargs='?', required=True, help="Output file")
    args = parser.parse_args(args=argv)

    df = pd.read_csv(args.input, sep=',')
    res = []
    data = df.to_dict('records')
    logger.info("Read {}".format(len(data)))
    for d in data:
        ld = logData(d)
        res.append([ld.date, ld.company, ld.entries, ld.lines, ld.recommended, ld.trained, ld.trained_date, ld.time])

    df = pd.DataFrame(res,
                      columns=["date", "company", "entries", "lines", "recommended", "trained", "trained_date", "time"])

    df.to_parquet(args.output, engine="fastparquet")
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
