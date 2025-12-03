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

def load_data(data_path: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    files = glob.glob(os.path.join(f"{data_path}", '*' ))
    df_list = []
    for file in files:
        temp_df = read_file(file)
        if temp_df is not None:
            temp_df.columns = temp_df.columns.str.strip()
            df_list.append(temp_df)
        else:
            return None  #some  msg would be nice
    users, orders, books = df_list
    return users, orders, books

def create_big_df(users: pd.DataFrame, orders: pd.DataFrame, books: pd.DataFrame) -> pd.DataFrame:
    big_df = orders.copy()
    big_df = big_df.merge(books, left_on='book_id', right_on=':id', how='left')
    big_df = big_df.merge(users, left_on='user_id', right_on='id', how='left')
    return big_df


if __name__ == "__main__":
    users, orders, books = load_data("data/DATA1")
    main_df = create_big_df(users, orders, books)
