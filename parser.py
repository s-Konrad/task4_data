import sys
from typing import Tuple

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
    df_list = {'users': None, 'orders': None, 'books': None}
    for file in files:
        temp_df = read_file(file)
        if temp_df is not None:
            temp_df.columns = temp_df.columns.str.strip().str.replace(':', '')

        else:
            return None  #some  msg would be nice

        if 'users' in file:
            df_list['users'] = temp_df
        if 'orders' in file:
            df_list['orders'] = temp_df
        if 'books' in file:
            df_list['books'] = temp_df

    return df_list['users'], df_list['orders'], df_list['books']

def create_big_df(users: pd.DataFrame, orders: pd.DataFrame, books: pd.DataFrame) -> pd.DataFrame:
    big_df = orders.copy()
    big_df = big_df.merge(books, left_on='book_id', right_on='id', how='left')
    big_df = big_df.merge(users, left_on='user_id', right_on='id', how='left')
    big_df = big_df.drop(columns=['id_y', 'id'])
    big_df = big_df.rename(columns={'id_x': 'order_id'})
    return big_df

def handle_datetime(df: pd.DataFrame) -> None:
    if 'timestamp' in df.columns:
        df['timestamp'] = (df['timestamp']
                           .str.replace('A.M.', 'AM')
                           .str.replace('P.M.', 'PM')
                           .str.replace(',', ' '))

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date_str'] = df['timestamp'].dt.strftime('%Y-%m-%d')

def parse_currency(value: str) -> float:

    value = value.strip().lower()
    is_euro = '€' in value or 'eur' in value
    value = remove_currency_signs(value)

    value = ".".join([substr for substr in value.split('.') if substr != ''], )
    value = float(value)

    if is_euro:
        value *= 1.2

    return round(value, 2)

def remove_currency_signs(value):
    for char in ['$', '€', '¢', ',']:
        value = value.replace(char, '.')
    value = "".join([c for c in value if c.isdigit() or c == '.'])
    return value

def normalize_numeric(df: pd.DataFrame) -> None:
    df['quantity'] = pd.to_numeric(df['quantity']).fillna(0)
    price = df['unit_price'].apply(parse_currency)
    df['unit_price'] = pd.to_numeric(price).fillna(0)
    df['paid_price'] = pd.to_numeric(df['unit_price'] * df['quantity'])

def clean_data():
    handle_datetime(main_df)
    normalize_numeric(main_df)
# ================================ Task 1 ================================
def analyze_revenue(df):
    daily_rev = df.groupby('date_str')['paid_price'].sum().reset_index()

    top_5 = daily_rev.sort_values('paid_price', ascending=False).head(5)

    return top_5

# ================================ Task 2 ================================
def create_sets(author: str) -> Tuple[str, ...]:
    authors = sorted([a.strip() for a in author.split(',')])
    return tuple(authors)

def find_sets_of_authors(df) -> Tuple[pd.DataFrame, int]:
    df['author'] = df['author'].apply(create_sets)
    unique_authors = df['author'].nunique()
    return df, unique_authors

# ================================ Task 3 ================================
def most_popular_authors(df) -> pd.DataFrame:
    df, _ = find_sets_of_authors(df)
    sold_books = df.groupby('author')['quantity'].sum().reset_index()
    most_popular_author = sold_books.sort_values('quantity', ascending=False).head(1)
    return most_popular_author

# ================================ Task 5 ================================
def get_daily_revenue(df) -> pd.DataFrame:
    revenue = df.groupby('date_str')['paid_price'].sum().reset_index()
    return revenue.sort_values('date_str')

def graph_revenue(df) -> None:
    chart_df = get_daily_revenue(df)
    st.subheader("Daily Revenue")
    st.line_chart(chart_df.set_index('date_str')['paid_price'])


if __name__ == "__main__":
    users, orders, books = load_data("data/DATA1")
    main_df = create_big_df(users, orders, books)
    clean_data()

    top_5 = analyze_revenue(main_df)
    st.subheader("1 - Top 5 revenue")
    st.dataframe(top_5)

    _, unique_authors = find_sets_of_authors(books)
    st.subheader("2 - Number of unique authors sets")
    st.metric("", unique_authors)

    best_author = most_popular_authors(main_df)
    st.subheader("Most Popular Author")
    st.dataframe(best_author)

    revenue = get_daily_revenue(main_df)
    graph_revenue(main_df)
