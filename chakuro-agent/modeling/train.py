# from sklearn.ensemble import RandomForestClassifier
from sklearn.externals import joblib
from xgboost import XGBClassifier
import pickle
import time
from .utility import working_dir, sha3
from logzero import logger as log
import sys
import numpy as np


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Bad arguments. Should be either bundled or single.')
        exit(1)
    target = sys.argv[1]

    train_indices = []
    test_indices = []
    if target == 'bundled':
        dg = pickle.load(open(working_dir / 'train.pkl', 'rb'))
        X, y = dg.X, dg.y
        train_indices = dg.index
        dgt = pickle.load(open(working_dir / 'test.pkl', 'rb'))
        Xt, yt = dgt.X, dgt.y
        test_indices = dgt.index

    elif target == 'single':
        Xs, ys = [], []
        with open(working_dir / 'training_list.txt') as f:
            for name in f:
                name = name.strip()
                if not name:
                    break
                try:
                    dg = pickle.load(open(working_dir / 'extraction' / f'{sha3(name)}.pkl', 'rb'))
                    Xs.append(dg.X)
                    ys.append(dg.y)
                    old_length = 0 if not train_indices else train_indices[-1]
                    train_indices.extend(i + old_length for i in dg.index)
                except FileNotFoundError:
                    log.warn(f'Not found {name}: {sha3(name)}')
        X = np.concatenate(Xs)
        y = np.concatenate(ys)
        Xs, ys = [], []
        with open(working_dir / 'testing_list.txt') as f:
            for name in f:
                name = name.strip()
                if not name:
                    break
                dg = pickle.load(open(working_dir / 'extraction' / f'{sha3(name)}.pkl', 'rb'))
                Xs.append(dg.X)
                ys.append(dg.y)
                old_length = 0 if not test_indices else test_indices[-1]
                test_indices.extend(i + old_length for i in dg.index)

        Xt = np.concatenate(Xs)
        yt = np.concatenate(ys)
    else:
        print('Bad arguments. Should be either bundled or single.')
        exit(1)

    log.info(f'Training dataset size: {X.shape}, {len(train_indices)}')
    log.info(f'Testing dataset size : {Xt.shape}, {len(test_indices)}')

    # Train the model
    start_time = time.time()
    # model = RandomForestClassifier(n_estimators=100, min_samples_leaf=7,
    #                                random_state=0, n_jobs=-1)
    model = XGBClassifier(n_estimators=100,
                          max_depth=4,
                          booster='gbtree',
                          learning_rate=0.2,
                          colsample_bylevel=0.8,
                          max_delta_step=1,
                          silent=True,
                          n_jobs=4,
                          random_state=0)
    model.fit(X, y)
    log.info(f'Fitting model took {time.time() - start_time}')
    joblib.dump(model, working_dir / 'model.model', protocol=4, compress=9)

    # Validate the model
    start_time = time.time()
    random_successful = 0.
    model_successful = 0.
    start = 0
    prob_all = model.predict_proba(Xt)

    # print(test_indices)
    for i in test_indices:
        end = i
        y = yt[start:end]
        if y.sum() != 1:
            log.warn(f'Sum of y is not 1, {(y.sum(), start, end, y)}')
        random_successful += 1 / (end - start)

        prob = prob_all[start:end, 1]
        if yt[start + prob.argmax()] > 0:
            model_successful += 1
        start = end

    log.info(f'Prediction took    {time.time() - start_time}')
    length = len(test_indices)
    log.info(f'Random successful rate: {random_successful} / {length} = {random_successful / length}')
    log.info(f'Model successful rate : {model_successful} / {length} = {model_successful / length}')