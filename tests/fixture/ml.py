from sklearn import metrics
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score

X, y = load_iris(True)
model = RandomForestClassifier(100)
scorer = 'f1_micro'
score = cross_val_score(model, X, y, cv=10)

print(f'score: {score.mean():.2%}')
