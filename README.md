# FeatureEngineering & AutoML
This is the Version Control of the code for the Masterthesis of Bastian Schäfer, an Computer Science (AI) student at Albert-Ludwigs Universität Freiburg.

The Masterthesis is conducted on the topic of Feature Engineering in the context of AutoML.

## Get it Running:
#### Installation:
`pip install -r requirements.txt`

#### Execution:
1. Choose option for dataset in the line `X_original, X_test_original, y, y_test = get_dataset(option=2)` in file src/amltk/main.py
   - Option 1: california-housing dataset from OpenFE example
   - Option 2: cylinder-bands dataset from OpenFE benchmark
   - Option 3: balance-scale dataset from OpenFE benchmark (not working)
   - Option 4: black-friday dataset from AMLB (long execution time)
2. Choose feature engineering methods and add them to the final dataframe in order to see the results:
   1. Get feature-engineered features by using the method from the corresponding file. Example: get_openFE_features from file src/amltk/feature_engineering/open_fe.py
   2. Get Cross-validation evaluator by calling get_cv_evaluator() method from the file src/amltk/evaluation/get_evaluator.py
   3. Optimize the pipeline and receive the history by calling e.g. history_openfe = pipeline.optimize(...)
   4. Convert history to a pandas dataframe: df_openFE = history_openFE.df()
   5. Append the dataframe with the history to one as done in line `df = pd.concat([df_original, df_sklearn, df_autofeat, df_openFE], axis=0)`
3. Execute `python3 src/amltk/pipeline/main.py`
<br>&rarr; See results in src/amltk/results/results.parquet
4. Adapt the first codeblock in the src/amltk/results/analysis.ipynb file in the following way:
   1. Make sure, that the number of max_trials (src/amltk/main.py) still equals 10 and set the `part_size = 10` value to exactly the same value
   2. Add all labels for all the methods used
5. Execute the file analysis.ipynb and receive all plots from the different accuracy metrics in case the runs were successful

#### Execution on MetaCluster:
1. Choose option (see above)
2. `sbatch scripts/meta/run.sh`
<br>&rarr; See results in logs/AMLTK_Pipeline-_BatchJobID_.out

## Explanation of the Results:
- The first 10 lines of the table are the results of 10 proposed models of the AutoML Pipeline on the original data (without Feature Engineering).
- All following lines (in packages of 10 lines each) are the results of proposed methods for AutoML with feature engineered data.

### First Insights
#### OpenFE 
- The test accuracy of the best performing model of the different splits is usually better on the original data.
- The mean of the training accuracy is usually higher over all the 10 models for the feature-engineered data.
- The mean of the validation accuracy is usually higher over all the 10 models for the feature-engineered data.
- The mean of the test accuracy is usually higher over all the 10 models for the feature-engineered data.
#### sklearn FE
- The data with the sklearn FE has a very high mean accuracy, while the std accuracy is slightly lower in comparison to the original data.
- The metric accuracy is much higher for the sklearn FE data than for the original data.
- The std accuracy is very low for both, original and FE data in all dataset splits.
- Regarding the test data, the original data outperforms the FE data.
