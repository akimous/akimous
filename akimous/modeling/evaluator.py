import pickle
import time

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.externals import joblib

dg = pickle.load(open('/Users/ray/Code/Working/single.pkl', 'rb'))
print('Dataset size:', dg.X.shape, len(dg.index))

train_test_boundary = dg.index[len(dg.index)//2]
X, y = dg.X[:train_test_boundary], dg.y[:train_test_boundary]
Xt, yt = dg.X[train_test_boundary:], dg.y[train_test_boundary:]
idxt = [i - train_test_boundary for i in dg.index[len(dg.index)//2+1:]]
print('train_test_boundary', train_test_boundary)


def evaluate(Xt, yt, index, model):
    start_time = time.time()
    dummy_successful = 0.
    model_successful = 0.
    start = 0

    prob_all = model.predict_proba(Xt)
    
    for i in range(len(index)):
        end = index[i]
        y = yt[start:end]
        if y.sum() != 1:
            print('warning: sum of y is not 1', y.sum(), start, end, y)
        dummy_successful += 1 / (end-start)
        
        prob = prob_all[start:end, 1]
        if yt[start+prob.argmax()] > 0:
            model_successful += 1
            
        start = end
        
    dummy_successful /= len(index)
    model_successful /= len(index)
    
    return {
        'dummy_successful_rate': dummy_successful,
        'model_successful_rate': model_successful,
        'time': time.time() - start_time
    }


start_time = time.time()
model = RandomForestClassifier(n_estimators=100, min_samples_leaf=1,
                               random_state=0, n_jobs=-1)
# model = GradientBoostingClassifier(n_estimators=100, learning_rate=.25, max_depth=6,
                                   # subsample=.8, max_features=.5, random_state=0, verbose=1)
model.fit(X, y)
print(f'fitting model took {time.time() - start_time}')
joblib.dump(model, '/Users/ray/Code/Working/single.model')
# model.n_jobs = 1
print(evaluate(Xt, yt, idxt, model))
