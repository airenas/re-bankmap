import argparse
import sys

import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle
from tensorflow.python.keras.callbacks import ModelCheckpoint, EarlyStopping

from egs.cmp_matrix.local.inspect_data import load_data
from src.utils.logger import logger


def main(argv):
    parser = argparse.ArgumentParser(description="Trains on features",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Initial data")
    parser.add_argument("--out", nargs='?', required=True, help="Model output file")
    parser.add_argument("--hidden", nargs='?', default=300, help="Hidden layer size")
    parser.add_argument("--batch", nargs='?', default=32, help="Batch size")
    args = parser.parse_args(args=argv)

    # try make results reproducible, but does not work for GPU
    # https://stackoverflow.com/questions/51249811/reproducible-results-in-tensorflow-with-tf-set-random-seed
    tf.random.set_seed(1)

    logger.info("Starting")
    data_df = load_data(args.input)
    logger.info("sample data")
    print(data_df.head(10), sep='\n\n')
    true_d = data_df[data_df['y_same'] == 1]
    false_d = data_df[data_df['y_same'] == 0]
    false_d = shuffle(false_d)[0:len(true_d) * 2]
    data_df = pd.concat([true_d, false_d])
    data_df.to_csv('out.csv')
    data = data_df.to_numpy()
    data_train, data_val = train_test_split(data, test_size=0.05, shuffle=True, random_state=1)
    logger.info("Data len train: {}".format(len(data_train)))
    logger.info("Data len val  : {}".format(len(data_val)))
    # Model architecture
    hidden = int(args.hidden)
    batch_size = int(args.batch)
    logger.info("Hidden      : {}".format(hidden))
    logger.info("Batch size: : {}".format(batch_size))

    logger.info("shape: {}".format(data.shape))
    print(data)
    logger.info("shape: {}".format(data[0].shape))
    print(data[0])
    yp = data.shape[1]
    logger.info("shape: {}".format(data[:, : yp - 1].shape))
    print(data[:, : yp - 1])
    logger.info("shape: {}".format(data[:, yp - 1].shape))
    print(data[:, yp - 1])

    params = [1]

    out = [p for p in params]
    out.append(yp - 1)
    df_out = data_df.iloc[:,out]
    df_out.to_csv('out_train.csv')
    inp_l = len(params)  # yp - 1
    input = tf.keras.layers.Input(shape=inp_l)
    output = input
    # output = tf.keras.layers.Dense(hidden, activation="relu")(output)
    output = tf.keras.layers.Dense(1, activation="relu")(output)
    model = tf.keras.Model(input, output)
    model.summary()
    model.compile(optimizer=tf.keras.optimizers.Adam(), loss="binary_crossentropy")

    def make_train_dataset(data):
        x = data[:, params]
        y = data[:, -1]
        return tf.data.Dataset.from_tensor_slices((x, y))

    def map_and_batch(ds, batch_size):
        return ds.batch(batch_size=batch_size).prefetch(tf.data.AUTOTUNE)

    train_ds = map_and_batch(make_train_dataset(data_train), batch_size)
    val_ds = map_and_batch(make_train_dataset(data_val), batch_size)

    checkpoint = ModelCheckpoint(filepath=args.out + "-val",  # "ep-{epoch:02d}",
                                 monitor='val_loss',
                                 verbose=1,
                                 save_best_only=True,
                                 mode='min')
    es = EarlyStopping(monitor='val_loss', mode='min', verbose=1, patience=10)

    model.fit(train_ds, validation_data=val_ds, epochs=150, verbose=1, callbacks=[checkpoint])
    model.summary(150)
    logger.info('Saving tf model ...')
    tf.keras.models.save_model(model, args.out)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
