import pickle

from sklearn.ensemble import RandomForestClassifier
from sklearn.externals import joblib

from .utility import WORKING_DIR

OUTPUT_FILE = f'{WORKING_DIR}model.pkl'

dg = pickle.load(open(f'{WORKING_DIR}dataset.pkl', 'rb'))
print(dg.X.shape, len(dg.index))

model = RandomForestClassifier(n_estimators=100, min_samples_leaf=1)
model.fit(dg.X, dg.y)
joblib.dump(model, OUTPUT_FILE)

print('Model saved to', OUTPUT_FILE)
