#!/usr/bin/env python3

import logging
import pickle
import argparse
import socket
import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

DATA_FILE  = 'apache_dataset_modified.csv'
MODEL_FILE = 'model/scai_classifier.pkl'
FEATURES   = ['map', 'lactate', 'cardiac_index', 'urine_output', 'creatinine']
TARGET     = 'SCAI_Stage'

format_str = (
    f'[%(asctime)s {socket.gethostname()}] '
    '%(filename)s:%(funcName)s:%(lineno)s - %(levelname)s: %(message)s'
)

parser = argparse.ArgumentParser()
parser.add_argument('-l', '--loglevel',
                    type=str,
                    required=False,
                    default='WARNING',
                    help='set log level to DEBUG, INFO, WARNING, ERROR, or CRITICAL')
args = parser.parse_args()

logging.basicConfig(level=args.loglevel, format=format_str)


def load_and_clean_data(filepath: str) -> pd.DataFrame:
    """
    Loads the dataset and drops rows with MAP of 0 as these are
    likely data artifacts rather than real clinical values.

    Args:
        filepath: Path to the CSV file.

    Returns:
        data: Cleaned pandas DataFrame.
    """
    logging.info(f'Loading dataset from {filepath}')
    data = pd.read_csv(filepath)
    logging.info(f'Raw dataset shape: {data.shape}')

    data = data[data['map'] > 0]
    logging.info(f'After dropping MAP=0 rows: {data.shape}')

    return data


def split_data(data: pd.DataFrame) -> tuple:
    """
    Splits the dataset into training and test sets.

    Args:
        data: Cleaned pandas DataFrame.

    Returns:
        X_train, X_test, y_train, y_test: Split datasets.
    """
    logging.info('Splitting data into training and test sets')
    X = data[FEATURES]
    y = data[TARGET]

    return train_test_split(X, y, test_size=0.3, stratify=y, random_state=1)


def fit_pipeline(X_train, y_train):
    """
    Fits a pipeline that standardizes data then applies a
    linear classifier using the Perceptron algorithm.

    Args:
        X_train: Training independent variables.
        y_train: Training dependent variables.

    Returns:
        pipeline: Trained pipeline.
    """
    logging.info('Fitting pipeline with StandardScaler and SGDClassifier')
    pipeline = Pipeline([
        ('scaler',     StandardScaler()),
        ('classifier', SGDClassifier(loss='perceptron', alpha=0.01))
    ])
    pipeline.fit(X_train, y_train)
    return pipeline


def save_model(model, filename: str) -> None:
    """
    Saves a trained model to a file using pickle.

    Args:
        model:    Trained pipeline to save.
        filename: Path to save the model to.

    Returns:
        None
    """
    logging.info(f'Saving model to {filename}')
    with open(filename, 'wb') as f:
        pickle.dump(model, f)


def main():
    try:
        data = load_and_clean_data(DATA_FILE)

        print('Class distribution:')
        print(data[TARGET].value_counts())

        X_train, X_test, y_train, y_test = split_data(data)

        pipeline = fit_pipeline(X_train, y_train)

        accuracy_train = accuracy_score(y_train, pipeline.predict(X_train))
        accuracy_test  = accuracy_score(y_test,  pipeline.predict(X_test))

        logging.info(f'pipeline train accuracy = {accuracy_train}')
        logging.info(f'pipeline test accuracy = {accuracy_test}')

        print(f'pipeline train accuracy = {round(accuracy_train, 4)}')
        print(f'pipeline test accuracy = {round(accuracy_test, 4)}')

        save_model(pipeline, MODEL_FILE)

    except Exception as e:
        logging.error(f'Error: {e}')


if __name__ == '__main__':
    main()