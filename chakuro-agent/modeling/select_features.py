from sklearn.ensemble import RandomForestClassifier
from .train import load_extracted_features, test_model
from .utility import working_dir
from logzero import logger as log
import logzero
import numpy as np

logzero.logfile(working_dir / 'feature_selection.log')

if __name__ == "__main__":
    X, y, train_indices, Xt, yt, test_indices, dg = load_extracted_features()
    feature_names = np.array(list(dg.name_to_feature_index.keys()))
    model = RandomForestClassifier(n_estimators=100, min_samples_split=3, random_state=0, n_jobs=-1)

    feature_mask = np.ones_like(X[0], dtype='?')
    model.fit(X, y)
    _, successful_count = test_model(model, Xt, yt, test_indices)

    iteration = 0
    dirty = True
    while dirty:
        iteration += 1
        dirty = False
        log.info(f'Iteration #{iteration}')
        log.info(np.array(feature_mask, dtype='int'))
        log.info(f'Baseline accuracy: {successful_count / len(test_indices):.2%} '
                 f'with {feature_mask.sum()} features')

        importances = model.feature_importances_
        argsort = importances.argsort()

        # remove features with 0 importance
        new_feature_mask = feature_mask.copy()
        secondary_mask = np.ones(feature_mask.sum(), dtype='?')
        for a in argsort:
            if importances[a] == 0:
                secondary_mask[a] = 0
                new_feature_mask[feature_mask] = secondary_mask
                dirty = True
                log.warning(f'Feature #{a:<3}: {feature_names[feature_mask][a]} removed for 0 importance.')
        if dirty:
            model.fit(X[:, new_feature_mask], y)
            _, new_successful_count = test_model(model, Xt[:, new_feature_mask], yt, test_indices)
            feature_mask = new_feature_mask
            successful_count = new_successful_count
            continue

        # remove features if the accuracy increases after removal
        for i, a in enumerate(argsort):
            new_feature_mask = feature_mask.copy()
            secondary_mask = np.ones(feature_mask.sum(), dtype='?')
            secondary_mask[a] = 0
            new_feature_mask[feature_mask] = secondary_mask

            model.fit(X[:, new_feature_mask], y)
            _, new_successful_count = test_model(model, Xt[:, new_feature_mask], yt, test_indices)
            log.debug(f'Trying to remove feature #{a:<3}: {feature_names[feature_mask][a]} '
                      f'with importance {importances[a]:.2%}, '
                      f'new accuracy is {new_successful_count / len(test_indices):.2%}')
            if new_successful_count >= successful_count:
                dirty = True
                feature_mask = new_feature_mask
                successful_count = new_successful_count
                log.warning(f'Feature #{a:<3}: {feature_names[feature_mask][a]} removed.')
                break
