import pandas as pd

from Autofeat.autofeat import AutoFeatRegressor, AutoFeatClassifier
from src.amltk.datasets.Datasets import preprocess_data, preprocess_target


def get_autofeat_features(train_x, train_y, test_x, task_hint) -> tuple[
    pd.DataFrame,
    pd.DataFrame
]:
    train_x = preprocess_data(train_x)
    train_y = preprocess_target(train_y)
    test_x = preprocess_data(test_x)

    feateng_steps = 1
    featsel_runs = 1
    transformations = ("1/", "exp", "log", "abs", "sqrt", "^2", "^3")

    if task_hint == 'regression':
        autofeat_regression = AutoFeatRegressor(
            verbose=1,
            # categorical_cols=cat_cols,
            feateng_steps=feateng_steps,
            featsel_runs=featsel_runs,
            always_return_numpy=False,
            transformations=transformations
        )
        train_x = autofeat_regression.fit_transform(train_x, train_y)
    elif task_hint == "classification":
        autofeat_classification = AutoFeatClassifier(
            verbose=1,
            # categorical_cols=cat_cols,
            feateng_steps=feateng_steps,
            featsel_runs=featsel_runs,
            always_return_numpy=False,
            transformations=transformations
        )
        train_x = autofeat_classification.fit_transform(train_x, train_y)
    return train_x, test_x