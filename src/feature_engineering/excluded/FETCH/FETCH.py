# https://github.com/liyaooi/FETCH

import pandas as pd

from src.feature_engineering.excluded.FETCH.method.main_attention import main


def get_fetch_features(train_x, train_y, test_x) -> tuple[
    pd.DataFrame,
    pd.DataFrame
]:
    print(train_x.shape)
    print(train_x.head(5))
    train_x, test_x = main(train_x, train_y, test_x)
    print(train_x.shape)
    print(train_x.head(5))
    return train_x, test_x
