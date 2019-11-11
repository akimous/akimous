import pickle
import time

import numpy as np
from logzero import logger
from xgboost import Booster, DMatrix, train

from ..utils import Timer, set_verbosity
from .utility import sha3, working_dir


def load_extracted_features():
    # Xs, ys = [], []
    train_indices = []
    test_indices = []

    height = 0
    width = 0
    # Pass 1: calculate array size
    with open(working_dir / 'training_list.txt') as f:
        for name in f:
            name = name.strip()
            if not name:
                break
            try:
                dg = pickle.load(
                    open(working_dir / 'extraction' / f'{sha3(name)}.pkl',
                         'rb'))
                height += dg.X.shape[0]
                width = dg.X.shape[1]
            except FileNotFoundError:
                logger.warning(f'Not found {name}: {sha3(name)}')

    X = np.empty([height, width], dtype=int)
    y = np.empty(height, dtype=int)
    Xi = 0

    # Pass 2: read training arrays
    with open(working_dir / 'training_list.txt') as f:
        for name in f:
            name = name.strip()
            if not name:
                break
            try:
                dg = pickle.load(
                    open(working_dir / 'extraction' / f'{sha3(name)}.pkl',
                         'rb'))
                length = len(dg.X)
                X[Xi:Xi + length, :] = dg.X
                y[Xi:Xi + length] = dg.y
                Xi += length
                old_length = 0 if not train_indices else train_indices[-1]
                train_indices.extend(i + old_length for i in dg.index)
            except FileNotFoundError:
                pass

    Xs, ys = [], []
    with open(working_dir / 'testing_list.txt') as f:
        for name in f:
            name = name.strip()
            if not name:
                break
            dg = pickle.load(
                open(working_dir / 'extraction' / f'{sha3(name)}.pkl', 'rb'))
            Xs.append(dg.X)
            ys.append(dg.y)
            old_length = 0 if not test_indices else test_indices[-1]
            test_indices.extend(i + old_length for i in dg.index)
    Xt = np.concatenate(Xs)
    yt = np.concatenate(ys)

    return X, y, train_indices, Xt, yt, test_indices, dg


def test_model(model: Booster, Xt, yt, test_indices):
    d_test = DMatrix(Xt, label=yt)
    random_successful = 0.
    model_successful = 0.
    prob_all = model.predict(d_test, True)

    start = 0
    for i in test_indices:
        end = i
        y = yt[start:end]
        if y.sum() != 1:
            logger.warning(f'Sum of y is not 1, {(y.sum(), start, end, y)}')
        random_successful += 1 / (end - start)

        prob = prob_all[start:end]
        if yt[start + prob.argmax()] > 0:
            model_successful += 1
        start = end

    return random_successful, model_successful


if __name__ == '__main__':
    set_verbosity(True)
    with Timer('loading feature'):
        X, y, train_indices, Xt, yt, test_indices, dg = load_extracted_features(
        )

    logger.info(f'Training dataset size: {X.shape}, {len(train_indices)}')
    logger.info(f'Testing dataset size : {Xt.shape}, {len(test_indices)}')

    d_train = DMatrix(X, label=y)
    # using external memory can have very bad accuracy
    # datasets.dump_svmlight_file(X, y, str(working_dir / 'svmlight.txt'))
    # d_train = DMatrix(
    # str(working_dir / 'svmlight.txt') + '#' +
    # str(working_dir / 'dtrain.cache'))

    # Train the model
    start_time = time.time()
    model = train(
        {
            'learning_rate': .2,
            'max_depth': 5,
            'colsample_bylevel': .8,
            'seed': 0,
            'tree_method': 'exact',
        }, d_train, 100)

    logger.info(f'Fitting model took {time.time() - start_time}\a')
    model.save_model(str(working_dir / 'model.xgb'))

    # Validate the model
    start_time = time.time()
    random_successful, model_successful = test_model(model, Xt, yt,
                                                     test_indices)
    logger.info(f'Prediction took    {time.time() - start_time}')
    length = len(test_indices)
    logger.info(
        f'Random successful rate: {random_successful} / {length} = {random_successful / length}'
    )
    logger.info(
        f'Model successful rate : {model_successful} / {length} = {model_successful / length}\a'
    )
