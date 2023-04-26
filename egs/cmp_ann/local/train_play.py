import argparse
import pickle
import sys
from builtins import enumerate

import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from tensorflow.python.keras.callbacks import EarlyStopping
from tqdm import tqdm

from bankmap.logger import logger
from egs.cmp_ann.local.make_features import Feature
from egs.cmp_ann.local.model import create_model
from egs.cmp_ann.local.similarity import params_count


def get_one_train_data(feat: Feature, model):
    res = model.predict(tf.constant(feat.arr_v), batch_size=1000, verbose=0)

    bi, wi = -1, -1
    for i, e in enumerate(feat.arr_it):
        if (bi == -1 or res[i][0] > res[bi][0]) and feat.rec_type == e[0] and feat.rec_id == e[1]:  # good case
            bi = i
        if (wi == -1 or res[i][0] > res[wi][0]) and (feat.rec_type != e[0] or feat.rec_id != e[1]):  # wrong case
            wi = i
    if bi > -1 and wi > -1:
        return [feat.arr_v[bi] + [1], feat.arr_v[wi] + [0]], res[bi][0] > res[wi][0]
    if wi > -1:
        return [feat.arr_v[wi] + [0]], None
    return [], None


def create_train_data(file, model):
    file.seek(0, 0)
    size = pickle.load(file)
    res = []
    with tqdm(desc="predicting", total=size) as pbar:
        c, err, skip = 0, 0, 0
        for feat in load_features(file):
            pbar.update(1)
            c += 1
            x, ok = get_one_train_data(feat, model)
            if ok is not None:
                err += 1 if not ok else 0
            else:
                skip += 1
            res += x
    return np.array(res), c, err, skip


def load_features(f):
    while True:
        try:
            yield pickle.load(f)
        except EOFError:
            break


def main(argv):
    parser = argparse.ArgumentParser(description="Predicts similarities for all item",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Input features pickle file")
    parser.add_argument("--out", nargs='?', required=True, help="Model output file")
    args = parser.parse_args(args=argv)

    logger.info("Starting")

    input_count = params_count()
    model = create_model(input_count)
    f = open(args.input, "rb")

    data, count, err, skip = create_train_data(f, model)
    logger.info("acc {:.3f}, {}/{} (skip {})".format((count - err - skip) / count, err, count, skip))

    batch_size = 32

    params = [i for i in range(input_count)]

    def make_train_dataset(_data):
        x = _data[:, params]
        y = _data[:, -1]
        return tf.data.Dataset.from_tensor_slices((x, y))

    def map_and_batch(ds, batch_size):
        return ds.batch(batch_size=batch_size).prefetch(tf.data.AUTOTUNE)

    # checkpoint = ModelCheckpoint(filepath=args.out + "-val",  # "ep-{epoch:02d}",
    #                              monitor='val_loss',
    #                              verbose=1,
    #                              save_best_only=True,
    #                              mode='min')
    es = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=10)

    be = 1000000
    errs = []
    for i in range(7):
        data_train, data_val = train_test_split(data, test_size=0.05, shuffle=True, random_state=1)
        logger.info("Data len train: {}".format(len(data_train)))
        logger.info("Data len val  : {}".format(len(data_val)))

        train_ds = map_and_batch(make_train_dataset(data_train), batch_size)
        val_ds = map_and_batch(make_train_dataset(data_val), batch_size)
        model.fit(train_ds, validation_data=val_ds, epochs=300, verbose=1, callbacks=[es])
        data, count, err, skip = create_train_data(f, model)
        errs.append(err)
        logger.info("acc {:.3f}, {}/{} (skip {})".format((count - err - skip) / count, err, count, skip))
        logger.info("errs {}".format(errs))
        logger.info('Saving tf model to {}_{}'.format(args.out, i))
        tf.keras.models.save_model(model, "{}_{}".format(args.out, i))
        if err < be:
            be = err
            logger.info('Saving best tf model ...')
            tf.keras.models.save_model(model, args.out)
        else:
            logger.info('skip save')

    f.close()
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
