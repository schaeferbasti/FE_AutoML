# https://github.com/numb3r33/fgcnn
from boruta import BorutaPy

import pandas as pd
from sklearn.ensemble import RandomForestClassifier


def get_boruta_features(train_x, train_y, test_x) -> tuple[
    pd.DataFrame,
    pd.DataFrame
]:
    rf = RandomForestClassifier(n_jobs=-1, class_weight='balanced', max_depth=5)
    feat_selector = BorutaPy(rf, n_estimators="auto", verbose=2)

    for column in train_x.select_dtypes(include=['object', 'category']).columns:
        train_x[column], uniques = pd.factorize(train_x[column])
    for column in test_x.select_dtypes(include=['object', 'category']).columns:
        test_x[column], uniques = pd.factorize(test_x[column])
    train_y = pd.DataFrame(train_y)
    for column in train_y.select_dtypes(include=['object', 'category']).columns:
        train_y[column], uniques = pd.factorize(train_y[column])

    train_x_np = train_x.values
    train_y_np = train_y.values
    test_x_np = test_x.values

    feat_selector.fit(train_x_np, train_y_np.ravel())

    # Transform the training and testing data
    train_x_selected = feat_selector.transform(train_x_np)
    test_x_selected = feat_selector.transform(test_x_np)

    # Convert the transformed data back to DataFrame
    train_x_selected_df = pd.DataFrame(train_x_selected, columns=train_x.columns[feat_selector.support_])
    test_x_selected_df = pd.DataFrame(test_x_selected, columns=test_x.columns[feat_selector.support_])

    print(train_x_selected_df.columns)
    print(test_x_selected_df.columns)
    return train_x_selected_df, test_x_selected_df
