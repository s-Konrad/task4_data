import sys

import pandas as pd
import numpy as np
import streamlit as st
import networkx as nx
import os
import glob
import yaml

st.set_page_config(page_title="Sales dashboard", layout="wide")

def read_file(path):
    _, ext = os.path.splitext(path)
    try:
        if ext == ".csv":
            return pd.read_csv(path)
        if ext == ".parquet":
            return pd.read_parquet(path)
        if ext == ".yaml":
            with open(path, "r") as f:
                data = yaml.safe_load(f)
            return pd.json_normalize(data)
        return None
    except:
        return None

def load_data(data_path):
    files = glob.glob(os.path.join(f"{data_path}", '*' ))
    df_list = []
    for file in files:
        temp_df = read_file(file)
        if temp_df is not None:
            temp_df.columns = temp_df.columns.str.strip().str.lower()
            df_list.append(temp_df)


if __name__ == "__main__":
    load_data("data/DATA1")