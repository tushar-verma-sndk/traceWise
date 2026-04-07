import pandas as pd
from pathlib import Path


def load_test_registry(file_path="test_registry.xlsx"):
    path = Path(file_path)

    if not path.exists():
        return {}, []

    df = pd.read_excel(path)

    df = df.dropna(subset=["Test Name"])

    mapping = dict(zip(df["Test Name"], df["Test Suite"]))

    test_list = sorted(df["Test Name"].unique())

    return mapping, test_list