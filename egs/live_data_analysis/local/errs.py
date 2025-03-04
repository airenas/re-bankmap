import argparse
import sys

from jsonlines import jsonlines

from bankmap.logger import logger
from bankmap.utils.utils import json_str
from egs.live_data_analysis.local.prepare import Data, Rec


def main(argv):
    parser = argparse.ArgumentParser(description="Prepare errors file",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input file")
    args = parser.parse_args(args=argv)

    logger.info("Starting")
    logger.info("loading cmp file {}".format(args.input))
    lines = []
    with jsonlines.open(args.input) as reader:
        for (i, d) in enumerate(reader):
            if i == 0:
                logger.debug(f"Item: {d}")
            v = Data.from_dict(d)
            lines.append(v)

    logger.info(f"Read {len(lines)}")

    def count(name, f):
        c = 0
        for v in lines:
            if f(v):
                c += 1
        logger.info(f"{name}: {c}")
        return c

    def f(v: Data) -> bool:
        return True

    count("All", f)

    def f(v: Data) -> bool:
        return v.user.rec and v.user.no

    count("User set value", f)

    def f(v: Data) -> bool:
        return v.user.rec and v.user.no and v.bf.rec

    count("BF predicted", f)

    def f(v: Data) -> bool:
        return v.user.rec and v.user.no and v.bf.rec and v.bf.eq(v.user)

    count("BF OK", f)

    def f(v: Data) -> bool:
        return v.user.rec and v.user.no and v.bf.rec and not v.bf.eq(v.user)

    count("BF Fail", f)

    def f(v: Data) -> bool:
        return v.user.rec and v.user.no and v.ai.rec

    count("AI predicted", f)

    def f(v: Data) -> bool:
        return v.user.rec and v.user.no and v.ai.rec and v.ai.eq(v.user)

    count("AI OK", f)

    def f(v: Data) -> bool:
        return v.user.rec and v.user.no and v.ai.rec and not v.ai.eq(v.user)

    count("AI Fail", f)

    def f(v: Data) -> bool:
        return v.user.rec and v.user.no and (v.ai.rec or v.bf.rec)

    count("BF or AI predicted", f)

    def f(v: Data) -> bool:
        return v.user.rec and v.user.no and (v.ai.rec and v.ai.eq(v.user) or v.bf.rec and v.bf.eq(v.user))

    count("BF or AI OK", f)

    def f(v: Data) -> bool:
        return v.user.rec and v.user.no and (v.ai.rec and not v.ai.eq(v.user) and v.bf.rec and v.bf.eq(v.user))

    count("BF OK, AI Fail", f)

    def f(v: Data) -> bool:
        return v.user.rec and v.user.no and (v.ai.rec and v.ai.eq(v.user) and v.bf.rec and not v.bf.eq(v.user))

    count("BF Fail, AI OK", f)

    def cs_ok(r: Rec) -> bool:
        return r.confidence_score >= 0.99

    def f(v: Data) -> bool:
        return v.user.rec and v.user.no and cs_ok(v.ai)

    count("AI 99 predicted", f)

    def f(v: Data) -> bool:
        return v.user.rec and v.user.no and cs_ok(v.ai) and v.ai.eq(v.user)

    count("AI 99 OK", f)

    def f(v: Data) -> bool:
        return v.user.rec and v.user.no and cs_ok(v.ai) and not v.ai.eq(v.user)

    count("AI 99 Fail", f)

    count, ok, fail, rec, try_count = 0, 0, 0, 0, 0
    for v in lines:
        if v.user.rec:
            count += 1
            if v.ai.rec:
                try_count += 1
                rec += 1
                if v.ai.eq(v.user):
                    ok += 1
                else:
                    fail += 1

    if try_count:
        logger.info(f"Res AI rec {rec} (failed {fail}) from {count}, acc: {ok / try_count}, pred: {try_count / count}")
    else:
        logger.warn(f"No data")

    count, ok, fail, rec, try_count = 0, 0, 0, 0, 0
    for v in lines:
        if v.user.rec:
            count += 1
            if v.bf.rec:
                try_count += 1
                rec += 1
                if v.bf.eq(v.user):
                    ok += 1
                else:
                    fail += 1

    if try_count:
        logger.info(f"Res BF rec {rec} (failed {fail}) from {count}, acc: {ok / try_count}, pred: {try_count / count}")
    else:
        logger.warn(f"No data")

    for v in lines:
        if v.user.rec:
            count += 1
            if v.ai.rec:
                if not v.ai.eq(v.user):
                    print(json_str(v.to_dict()), file=sys.stdout)

    count, rec = 0, 0
    for v in lines:
        if v.user.rec:
            if v.ai.rec:
                if v.ai.eq(v.user) and not v.bf.eq(v.user):
                    count += 1
                    if v.bf.rec:
                        rec += 1
                        logger.debug(json_str(v.to_dict()))
    logger.info(f"AI ok, BF not {count}, rec {rec}")

    count, rec = 0, 0
    for v in lines:
        if v.user.rec:
            if v.bf.rec:
                if v.bf.eq(v.user) and not v.ai.eq(v.user):
                    count += 1
                    if v.ai.rec:
                        rec += 1
                        logger.debug(json_str(v.to_dict()))
    logger.info(f"BF ok, AI not {count}, rec {rec}")
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
