from sklearn.ensemble import RandomForestClassifier
from sklearn.externals import joblib
import pickle
import time
from utility import working_dir


if __name__ == "__main__":
    dg = pickle.load(open(working_dir / 'train.pkl', 'rb'))
    X, y = dg.X, dg.y
    print('Training dataset size:', X.shape, len(dg.index))

    dgt = pickle.load(open(working_dir / 'test.pkl', 'rb'))
    Xt, yt = dgt.X, dgt.y
    print('Testing dataset size :', Xt.shape, len(dgt.index))

    # Train the model
    start_time = time.time()
    model = RandomForestClassifier(n_estimators=100, min_samples_leaf=1,
                                   random_state=0, n_jobs=-1)
    model.fit(X, y)
    print(f'Fitting model took {time.time() - start_time}')
    joblib.dump(model, working_dir / 'model.model')

    # Validate the model
    start_time = time.time()
    random_successful = 0.
    model_successful = 0.
    start = 0
    prob_all = model.predict_proba(Xt)

    index = dgt.index
    for i in index:
        end = i
        y = yt[start:end]
        if y.sum() != 1:
            print('warning: sum of y is not 1', y.sum(), start, end, y)
        random_successful += 1 / (end - start)

        prob = prob_all[start:end, 1]
        if yt[start + prob.argmax()] > 0:
            model_successful += 1
        start = end

    print(f'Prediction took    {time.time() - start_time}')
    print(f'Random successful rate: {random_successful} / {len(index)} = {random_successful / len(index)}')
    print(f'Model successful rate : {model_successful} / {len(index)} = {model_successful / len(index)}')