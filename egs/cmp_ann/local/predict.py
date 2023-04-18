import argparse
import pickle
import sys
from builtins import enumerate

import tensorflow as tf
from tqdm import tqdm

from bankmap.logger import logger
from egs.cmp_ann.local.make_features import Feature
from egs.cmp_ann.local.train_play import load_features


def get_best_account(feat: Feature, model):
    res = model.predict(tf.constant(feat.arr_v), batch_size=1000, verbose=0)

    bi = -1
    for i, e in enumerate(feat.arr_it):
        if bi == -1 or res[i][0] > res[bi][0]:
            bi = i
    if bi > -1:
        return feat.arr_it[bi], feat.arr_v[bi], res[bi][0]
    return None, [], 0


def main(argv):
    parser = argparse.ArgumentParser(description="Predicts similarities for all item",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input features pickle file")
    parser.add_argument("--model", nargs='?', required=True, help="Input model")
    parser.add_argument("--out", nargs='?', required=True, help="Output file")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

    logger.info("loading model {}".format(args.model))
    model = tf.keras.models.load_model(args.model)
    model.summary(150)
    with open(args.input, "rb") as f:
        with open(args.out, "w") as f_out:
            size = pickle.load(f)
            with tqdm(desc="predicting", total=size) as pbar:
                for feat in load_features(f):
                    pbar.update(1)
                    best, sim, val = get_best_account(feat, model)
                    res = "{}:{}\t{}\t{}\t{}".format(best[0].to_s(), best[1] if best is not None else "", "", sim, val)
                    print(res, file=f_out)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
