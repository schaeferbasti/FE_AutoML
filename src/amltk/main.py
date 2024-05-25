from __future__ import annotations

import warnings
from pathlib import Path
import os.path

from amltk.optimization import Metric
from amltk.pipeline import Choice, Sequential, Split
from sklearn.metrics import get_scorer
from sklearn.preprocessing import *

from src.amltk.classifiers.Classifiers import *
from src.amltk.datasets.Datasets import *
from src.amltk.evaluation.Evaluator import get_cv_evaluator
from src.amltk.feature_engineering.AutoGluon import get_autogluon_features
from src.amltk.feature_engineering.Autofeat import get_autofeat_features
from src.amltk.feature_engineering.H2O import get_h2o_features
from src.amltk.feature_engineering.MLJAR import get_mljar_features
from src.amltk.feature_engineering.OpenFE import get_openFE_features
from src.amltk.feature_engineering.Sklearn import get_sklearn_features
from src.amltk.optimizer.RandomSearch import RandomSearch

warnings.simplefilter(action='ignore', category=FutureWarning)

preprocessing = Split(
    {
        "numerical": Component(SimpleImputer, space={"strategy": ["mean", "median"]}),
        "categorical": [
            Component(
                OrdinalEncoder,
                config={
                    "categories": "auto",
                    "handle_unknown": "use_encoded_value",
                    "unknown_value": -1,
                    "encoded_missing_value": -2,
                },
            ),
            Choice(
                "passthrough",
                Component(
                    OneHotEncoder,
                    space={"max_categories": (2, 20)},
                    config={
                        "categories": "auto",
                        "drop": None,
                        "sparse_output": False,
                        "handle_unknown": "infrequent_if_exist",
                    },
                ),
                name="one_hot",
            ),
        ],
    },
    name="preprocessing",
)


def safe_dataframe(df_collection, working_dir, dataset_name, fold):
    if fold is None:
        file_string = "results_" + str(dataset_name) + ".parquet"
    else:
        file_string = "results_" + str(dataset_name) + "_fold_" + str(fold) + ".parquet"
    results_to = working_dir / file_string
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    print(df_collection)
    print(f"Saving dataframe of results to path: {results_to}")
    df_collection.to_parquet(results_to)


rf_classifier = get_rf_classifier()
rf_pipeline = Sequential(preprocessing, rf_classifier, name="rf_pipeline")

# works on dataset 2 (not for continuous data)
mlp_classifier = get_mlp_classifier()
mlp_pipeline = Sequential(preprocessing, mlp_classifier, name="mlp_pipeline")

# works on dataset 2 (not on continuous data)
svc_classifier = get_svc_classifier()
svc_pipeline = Sequential(preprocessing, svc_classifier, name="svc_pipeline")

# works on dataset 2 (not on continuous data)
knn_classifier = get_knn_classifier()
knn_pipeline = Sequential(preprocessing, knn_classifier, name="knn_pipeline")

lgbm_classifier = get_lgbm_classifier()
lgbm_classifier_pipeline = Sequential(preprocessing, lgbm_classifier, name="lgbm_classifier_pipeline")

lgbm_regressor = get_lgbm_regressor()
lgbm_regressor_pipeline = Sequential(preprocessing, lgbm_regressor, name="lgbm_regressor_pipeline")

def main() -> None:
    rerun = False                               # Decide if you want to re-execute the methods on a dataset or use the existing files
    debugging = False                           # Decide if you want ot raise trial exceptions
    steps = 3                                   # Number of steps for autofeat
    num_features = 50                           # Number of features generated by MLJAR
    working_dir = Path("src/amltk/results")     # Path if running on Cluster
    # working_dir = Path("results")             # Path for local execution
    random_seed = 42                            # Set seed
    folds = 10                                  # Set number of folds (normal 10, test 1)

    # Choose set of datasets
    all_datasets = [1, 5, 14, 15, 16, 17, 18, 21, 22, 23, 24, 27, 28, 29, 31, 35, 36]
    small_datasets = [1, 5, 14, 16, 17, 18, 21, 27, 31, 35, 36]
    smallest_datasets = [14, 16, 17, 21, 35]  # n ~ 1000, p ~ 15
    big_datasets = [15, 22, 23, 24, 28, 29]
    test_new_method_datasets = [16]

    optimizer_cls = RandomSearch
    pipeline = lgbm_classifier_pipeline

    metric_definition = Metric(
        "accuracy",
        minimize=False,
        bounds=(0, 1),
        fn=get_scorer("accuracy"),
    )

    per_process_memory_limit = None  # (4, "GB")  # NOTE: May have issues on Mac
    per_process_walltime_limit = None  # (60, "s")

    if debugging:
        max_trials = 100000
        max_time = 60*60
        n_workers = 4
        # raise an error with traceback, something went wrong
        on_trial_exception = "raise"
        display = True
        wait_for_all_workers_to_finish = False
    else:
        max_trials = 100000
        max_time = 60*60
        n_workers = 4
        # Just mark the trial as fail and move on to the next one
        on_trial_exception = "continue"
        display = True
        wait_for_all_workers_to_finish = False

    df_collection = pd.DataFrame()
    df_collection_fold = pd.DataFrame()

    for fold in range(folds):
        print("\n\n\n*******************************\n Fold " + str(fold) + "\n*******************************\n")
        inner_fold_seed = random_seed + fold
        # Iterate over all chosen datasets
        for option in small_datasets:
            # Get train test split dataset
            train_x, train_y, test_x, test_y, task_hint, name = get_dataset(option=option)

            print("\n\n\n*******************************\n" + str(name) + "\n*******************************\n")
            file_name = "results_" + str(name) + "_fold_" + str(fold) + ".parquet"
            file = working_dir / file_name
            # Execute all FE methods if the file doesn't exist or the user wants to rerun the process
            if rerun or not os.path.isfile(file):
                print("Run FE methods on Dataset \n")
                """
                ############## Original Data ##############
                Use original data without feature engineering
    
                """
                print("Original Data")
                evaluator = get_cv_evaluator(train_x, train_y, test_x, test_y, inner_fold_seed,
                                             on_trial_exception, task_hint)

                history_original = pipeline.optimize(
                    target=evaluator.fn,
                    metric=metric_definition,
                    optimizer=optimizer_cls,
                    seed=inner_fold_seed,
                    process_memory_limit=per_process_memory_limit,
                    process_walltime_limit=per_process_walltime_limit,
                    working_dir=working_dir,
                    max_trials=max_trials,
                    timeout=max_time,
                    display=display,
                    wait=wait_for_all_workers_to_finish,
                    n_workers=n_workers,
                    on_trial_exception=on_trial_exception,
                )

                """
                ############## Feature Engineering with MLJAR ##############
                Use MLJAR Feature Generation and Selection
    
                """

                print("\n\nMLJAR Data")
                train_x_mljar, test_x_mljar = get_mljar_features(train_x, train_y, test_x, num_features)

                evaluator = get_cv_evaluator(train_x_mljar, train_y, test_x_mljar, test_y, inner_fold_seed,
                                             on_trial_exception,
                                             task_hint)

                history_mljar = pipeline.optimize(
                    target=evaluator.fn,
                    metric=metric_definition,
                    optimizer=optimizer_cls,
                    seed=inner_fold_seed,
                    process_memory_limit=per_process_memory_limit,
                    process_walltime_limit=per_process_walltime_limit,
                    working_dir=working_dir,
                    max_trials=max_trials,
                    timeout=max_time,
                    display=display,
                    wait=wait_for_all_workers_to_finish,
                    n_workers=n_workers,
                    on_trial_exception=on_trial_exception,
                )

                """
                ############## Feature Engineering with sklearn ##############
                Use self-implemented Feature Generation and Selection with the usage of the sklearn library
                
                """
                print("\n\nSklearn Data")
                train_x_sklearn, test_x_sklearn = get_sklearn_features(train_x, train_y, test_x)

                evaluator = get_cv_evaluator(train_x_sklearn, train_y, test_x_sklearn, test_y, inner_fold_seed,
                                             on_trial_exception, task_hint)

                history_sklearn = pipeline.optimize(
                    target=evaluator.fn,
                    metric=metric_definition,
                    optimizer=optimizer_cls,
                    seed=inner_fold_seed,
                    process_memory_limit=per_process_memory_limit,
                    process_walltime_limit=per_process_walltime_limit,
                    working_dir=working_dir,
                    max_trials=max_trials,
                    timeout=max_time,
                    display=display,
                    wait=wait_for_all_workers_to_finish,
                    n_workers=n_workers,
                    on_trial_exception=on_trial_exception,
                )

                """
                ############## Feature Engineering with autofeat ##############
                Use Feature Engineering from autofeat
            
                """
                print("\n\nautofeat Data")
                train_x_autofeat, test_x_autofeat = get_autofeat_features(train_x, train_y, test_x, task_hint, steps)

                evaluator = get_cv_evaluator(train_x_autofeat, train_y, test_x_autofeat, test_y, inner_fold_seed,
                                             on_trial_exception, task_hint)

                history_autofeat = pipeline.optimize(
                    target=evaluator.fn,
                    metric=metric_definition,
                    optimizer=optimizer_cls,
                    seed=inner_fold_seed,
                    process_memory_limit=per_process_memory_limit,
                    process_walltime_limit=per_process_walltime_limit,
                    working_dir=working_dir,
                    max_trials=max_trials,
                    timeout=max_time,
                    display=display,
                    wait=wait_for_all_workers_to_finish,
                    n_workers=n_workers,
                    on_trial_exception=on_trial_exception,
                )

                """
                ############## Feature Engineering with OpenFE ##############
                Use Feature Generation and Selection implemented by the OpenFE paper
            
                """
                print("\n\nOpenFE Data")
                train_x_openfe, test_x_openfe = get_openFE_features(train_x, train_y, test_x, 1)

                evaluator = get_cv_evaluator(train_x_openfe, train_y, test_x_openfe, test_y, inner_fold_seed,
                                             on_trial_exception, task_hint)

                history_openFE = pipeline.optimize(
                    target=evaluator.fn,
                    metric=metric_definition,
                    optimizer=optimizer_cls,
                    seed=inner_fold_seed,
                    process_memory_limit=per_process_memory_limit,
                    process_walltime_limit=per_process_walltime_limit,
                    working_dir=working_dir,
                    max_trials=max_trials,
                    timeout=max_time,
                    display=display,
                    wait=wait_for_all_workers_to_finish,
                    n_workers=n_workers,
                    on_trial_exception=on_trial_exception,
                )

                """
                ############## Feature Engineering with h2o ##############
                Use h2o Feature Generation and Selection
    
                """

                print("\n\nH2O Data")
                train_x_h2o, test_x_h2o = get_h2o_features(train_x, train_y, test_x)

                evaluator = get_cv_evaluator(train_x_h2o, train_y, test_x_h2o, test_y, inner_fold_seed, on_trial_exception,
                                             task_hint)

                history_h2o = pipeline.optimize(
                    target=evaluator.fn,
                    metric=metric_definition,
                    optimizer=optimizer_cls,
                    seed=inner_fold_seed,
                    process_memory_limit=per_process_memory_limit,
                    process_walltime_limit=per_process_walltime_limit,
                    working_dir=working_dir,
                    max_trials=max_trials,
                    timeout=max_time,
                    display=display,
                    wait=wait_for_all_workers_to_finish,
                    n_workers=n_workers,
                    on_trial_exception=on_trial_exception,
                )

                """
                ############## Feature Engineering with AutoGluon ##############
                Use AutoGluon Feature Generation and Selection
    
                """

                print("\n\nAutoGluon Data")
                train_x_autogluon, test_x_autogluon = get_autogluon_features(train_x, train_y, test_x)

                evaluator = get_cv_evaluator(train_x_autogluon, train_y, test_x_autogluon, test_y, inner_fold_seed,
                                             on_trial_exception,
                                             task_hint)

                history_autogluon = pipeline.optimize(
                    target=evaluator.fn,
                    metric=metric_definition,
                    optimizer=optimizer_cls,
                    seed=inner_fold_seed,
                    process_memory_limit=per_process_memory_limit,
                    process_walltime_limit=per_process_walltime_limit,
                    working_dir=working_dir,
                    max_trials=max_trials,
                    timeout=max_time,
                    display=display,
                    wait=wait_for_all_workers_to_finish,
                    n_workers=n_workers,
                    on_trial_exception=on_trial_exception,
                )

                df_collection_fold.assign(
                    outer_fold=fold,
                    inner_fold_seed=inner_fold_seed,
                    max_trials=max_trials,
                    max_time=max_time,
                    optimizer=optimizer_cls.__name__,
                    n_workers=n_workers,
                )

                # Create Dataframes from FE methods and concat to one frame
                df_original = history_original.df()
                df_sklearn = history_sklearn.df()
                df_autofeat = history_autofeat.df()
                df_openFE = history_openFE.df()
                df_h2o = history_h2o.df()
                df_mljar = history_mljar.df()
                df_autogluon = history_autogluon.df()
                df_option = pd.concat([df_original, df_sklearn, df_autofeat, df_openFE, df_h2o, df_mljar, df_autogluon],
                                      axis=0)
                # Safe Dataframe for dataset
                safe_dataframe(df_option, working_dir, name, fold)
            else:
                # Read dataset from parquet (without executing all FE methods on the dataset)
                print("Read from Parquet")
                df_option = pd.read_parquet(file, engine='pyarrow')
            # Append frames from the datasets to one big frame
            df_collection_fold = df_collection_fold._append(df_option)
        # Safe fold dataframe
        df_collection_fold.assign(
            outer_fold=fold,
            inner_fold_seed=inner_fold_seed,
            max_trials=max_trials,
            max_time=max_time,
            optimizer=optimizer_cls.__name__,
            n_workers=n_workers,
        )
        safe_dataframe(df_collection_fold, working_dir, "collection", fold)
        df_collection = df_collection._append(df_collection_fold)
    # Safe big dataframe
    df_collection.assign(
        outer_fold=folds,
        inner_fold_seed=random_seed,
        max_trials=max_trials,
        max_time=max_time,
        optimizer=optimizer_cls.__name__,
        n_workers=n_workers,
    )
    safe_dataframe(df_collection, working_dir, "collection", None)


if __name__ == "__main__":
    main()
