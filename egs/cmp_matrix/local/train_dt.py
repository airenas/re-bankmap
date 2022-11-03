import argparse
import pickle
import sys

import pandas as pd
import tensorflow as tf
from matplotlib import pyplot as plt
from sklearn import tree
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.utils import shuffle

from egs.cmp_matrix.local.inspect_data import load_data
from src.utils.logger import logger


def main(argv):
    parser = argparse.ArgumentParser(description="Trains on features using DT",
                                     epilog="E.g. " + sys.argv[0] + "",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", nargs='?', required=True, help="Initial data")
    parser.add_argument("--out", nargs='?', required=True, help="Model output file")
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
    params = [0, 2, 3, 4]
    yp = data.shape[1]
    X = data_train[:, params]
    y = [str(d) for d in data_train[:, yp - 1]]
    y = data_train[:, yp - 1]

    logger.info("Shape X: {}".format(X.shape))

    dtree = DecisionTreeClassifier(max_depth=4)
    dtree = dtree.fit(X, y)
    tree.plot_tree(dtree, feature_names=['eq_name', 'eq_iban', 'doc_in_msg', 'till_due_date'])

    plt.savefig("out.svg")
    logger.info('Saving model ...')
    with open(args.out, "wb") as f:
        pickle.dump(dtree, f)
    logger.info("Done")


if __name__ == "__main__":
    main(sys.argv[1:])
