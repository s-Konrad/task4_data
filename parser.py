from typing import Tuple
import pandas as pd
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
    df['paid_price_USD'] = pd.to_numeric(df['unit_price'] * df['quantity'])

def clean_data(df: pd.DataFrame) -> None:
    handle_datetime(df)
    normalize_numeric(df)
# ================================ Task 1 ================================
def analyze_revenue(df):
    daily_rev = df.groupby('date_str')['paid_price_USD'].sum().reset_index()

    top_5 = daily_rev.sort_values('paid_price_USD', ascending=False).head(5)

    return top_5

# ================================ Task 2 ================================

def find_unique_users(df) -> pd.DataFrame:
    G = nx.Graph()

    for _, row in df.iterrows():
        uid_node = f"uid_{row['user_id']}"
        G.add_node(uid_node, type='user')

        if 'email' in df.columns and row['email']:
            G.add_edge(uid_node, f"email_{row['email']}")

        if 'phone' in df.columns and row['phone']:
            G.add_edge(uid_node, f"phone_{row['phone']}")

        if 'address' in df.columns and row['address']:
            G.add_edge(uid_node, f"addr_{row['address']}")

    components = list(nx.connected_components(G))

    id_mapping = {}

    for group_id, component in enumerate(components):
        real_id = group_id + 1
        for node in component:
            if node.startswith('uid_'):
                original_id = int(node.replace('uid_', ''))
                id_mapping[original_id] = real_id

    map_df = pd.DataFrame(list(id_mapping.items()), columns=['original_user_id', "unique_user_id"])
    map_df['original_user_id'] = pd.to_numeric(map_df['original_user_id'])
    map_df['unique_user_id'] = pd.to_numeric(map_df['original_user_id'])
    df = df.merge(map_df, left_on='user_id', right_on='original_user_id', how='left')
    df = df.drop(columns=['original_user_id'])

    return df

def count_unique_users(df):
    return df['unique_user_id'].nunique()

# ================================ Task 3 ================================
def create_sets(author: str) -> Tuple[str, ...]:
    authors = sorted([a.strip() for a in author.split(',')])
    return tuple(authors)

def find_sets_of_authors(df) -> Tuple[pd.DataFrame, int]:
    df['author'] = df['author'].apply(create_sets)
    unique_authors = df['author'].nunique()
    return df, unique_authors

# ================================ Task 4 ================================
def most_popular_authors(df) -> pd.DataFrame:
    sold_books = df.groupby('author')['quantity'].sum().reset_index()
    most_popular_author = sold_books.sort_values('quantity', ascending=False).head(1)
    return most_popular_author

# ================================ Task 5 ================================
def get_daily_revenue(df) -> pd.DataFrame:
    revenue = df.groupby('date_str')['paid_price_USD'].sum().reset_index()
    return revenue.sort_values('date_str')

def graph_revenue(df) -> None:
    chart_df = get_daily_revenue(df)
    st.subheader("Daily Revenue")
    st.line_chart(chart_df.set_index('date_str')['paid_price_USD'])

# ================================ Task 6 ================================

def get_best_spending_users(df) -> pd.DataFrame:
    users_spending_df = df.groupby('user_id')['paid_price_USD'].sum().reset_index()
    return users_spending_df.sort_values('paid_price_USD', ascending=False)


# ============================ Display methods ============================

def display_solution_1(df: pd.DataFrame) -> None:
    top_5 = analyze_revenue(df)
    st.subheader("1 - Top 5 revenue")
    st.dataframe(top_5)


def display_solution_2(df: pd.DataFrame) -> None:
    main_df = find_unique_users(df)
    st.subheader("2 - Number of unique users")
    num_unique_users = count_unique_users(main_df)
    st.metric("", num_unique_users)


def display_solution_3(books: pd.DataFrame) -> None:
    _, unique_authors = find_sets_of_authors(books)
    st.subheader("3 - Number of unique authors sets")
    st.metric("", unique_authors)


def display_solution_4(df: pd.DataFrame) -> None:
    best_author = most_popular_authors(df)
    st.subheader("4 - Most popular author")
    st.dataframe(best_author)


def display_solution_5(df: pd.DataFrame) -> None:
    st.subheader("5 - Greatest spending user")
    best_spending_users = get_best_spending_users(df)
    st.dataframe(best_spending_users)


def display_solution_6(df: pd.DataFrame) -> None:
    st.subheader("6 - Daily revenue")
    graph_revenue(df)


def render_dataset(data_path: str) -> None:
    main_df = get_df(data_path)

    display_solution_1(main_df)
    display_solution_2(main_df)
    display_solution_3(main_df)
    display_solution_4(main_df)
    display_solution_5(main_df)
    display_solution_6(main_df)


def get_df(data_path: str) -> pd.DataFrame:
    users, orders, books = load_data(data_path)
    main_df = create_big_df(users, orders, books)
    clean_data(main_df)
    return main_df

# ========================================================================

if __name__ == "__main__":
    st.title("Sales Dashboard")
    tab1, tab2, tab3 = st.tabs(["DATA1", "DATA2", "DATA3"])

    with tab1:
        render_dataset("data/DATA1")

    with tab2:
        render_dataset("data/DATA2")

    with tab3:
        render_dataset("data/DATA3")