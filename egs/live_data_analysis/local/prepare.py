import argparse
import sys

from jsonlines import jsonlines

from bankmap.data import e_str_e, e_str_ne, e_float
from bankmap.logger import logger
from bankmap.utils.utils import json_str


class Rec:
    def __init__(self, type, no, rec, cs = 0):
        self.type = type
        self.no = no
        self.rec = rec
        self.confidence_score = cs

    def to_dict(self):
        return {'type': self.type, 'no': self.no, 'rec': self.rec, 'cs': self.confidence_score}

    def eq(self, c):
        return self.type == c.type and self.no == c.no

    @classmethod
    def from_dict(cls, d):
        return Rec(d.get("type", ""), d.get("no", ""), d.get("rec", False), cs =d.get("cs", False))


class Data:
    def __init__(self, itemNo):
        self.itemNo = itemNo
        self.user = Rec("", "", False)
        self.bf = Rec("", "", False)
        self.ai = Rec("", "", False)

    # Method to serialize Data to dictionary
    def to_dict(self):
        return {
            'no': self.itemNo,
            'user': self.user.to_dict(),
            'bf': self.bf.to_dict(),
            'ai': self.ai.to_dict()
        }

    @classmethod
    def from_dict(cls, d):
        res = Data(d["no"])
        res.user = Rec.from_dict(d.get("user"))
        res.bf = Rec.from_dict(d.get("bf"))
        res.ai = Rec.from_dict(d.get("ai"))
        return res


def main(argv):
    parser = argparse.ArgumentParser(description="Prepare errors file",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file")
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    logger.info("loading docs map {}".format(args.input))
    tmp = {}
    with jsonlines.open(args.input) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            id = e_str_ne(d, "LineNo")
            v = tmp.setdefault(id, Data(id))
            provider = e_str_ne(d, "RecognitionProvider")
            rec = Rec(e_str_e(d, "RecognizedAccountType"), e_str_e(d, "RecognizedAccountNo"),
                    d["Recommended"], cs = e_float(d, "ConfidenceScore"))
            if provider == "Posted":
                v.user = rec
            elif provider == "Default":
                v.bf = rec
            elif provider == "External":
                v.ai = rec
            else:
                raise RuntimeError(f"unk provider {provider}")
    c = 0
    for v in tmp.values():
        print(json_str(v.to_dict()), file=sys.stdout)
        c += 1
    logger.info(f"Wrote {c}")
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
