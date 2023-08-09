import argparse
import sys

import pandas as pd

from bankmap.data import to_date
from bankmap.logger import logger


class LogData:
    def __init__(self, data):
        self.date = to_date(data.get("Sukurta", "no date")).strftime("%Y%m%d")
        self.time = to_date(data.get("Sukurta", "no date")).strftime("%H:%M:%S")
        self.actual = data.get("Recognized Account No. - Actual", "")
        self.bf = data.get("Recognized Account No.", "")
        self.ai = data.get("Recognized Account No. - External", "")
        self.ba = data.get("Bank Account No.", "")
        self.ext_no = data.get("External Document No.", "")
        self.ai_conf = data.get("Confidence Score - External", "")

    def to_s(self):
        return "{}\t{}\t{}\t{}\t{}\t{}".format(self.date, self.company, self.trained, self.entries, self.lines,
                                               self.recommended)


def main(argv):
    parser = argparse.ArgumentParser(description="Parses csv comparison file",
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
        ld = LogData(d)
        res.append(
            [ld.date, ld.time, ld.actual, ld.bf, ld.ai, ld.ba, ld.ext_no, ld.ai_conf])

    df = pd.DataFrame(res,
                      columns=["date", "time", "actual", "bf", "ai", "ba", "ext_no", "ai_conf"])

    df.to_parquet(args.output, engine="fastparquet")
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
