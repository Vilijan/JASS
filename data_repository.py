import pyodbc
import pandas as pd
import streamlit as st


def retrieve_db_cursor(username: str, password: str):
    server = '89.205.12.13'
    database_name = 'jass2019'
    cnxn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server +
        ';DATABASE=' + database_name +
        ';UID=' + username +
        ';PWD=' + password)
    cursor = cnxn.cursor()

    return cursor


@st.cache
def retrieve_db_data(username: str, password: str) -> pd.DataFrame:
    cursor = retrieve_db_cursor(username, password)

    employees = create_employees_csv(cursor)
    employees_map = {arr[1]: arr[0] for arr in employees[['IME', 'KORISNIK']].values}

    df = create_products_store_csv(cursor)

    df['employee_name'] = df['employee_id'].apply(lambda x: employees_map.get(x, 'Unknown'))

    return df


def create_df_from_table(cursor, table_name):
    cursor.execute(f'SELECT * FROM jass2019.dbo.{table_name}')
    columns = [column[0] for column in cursor.description]
    table_data = dict()
    for c_name in columns:
        table_data[c_name] = []

    for row in cursor:
        arr = list(row)
        for i in range(len(arr)):
            table_data[columns[i]].append(arr[i])

    return pd.DataFrame(data=table_data)


def create_products_store_csv(cursor):
    cursor.execute(f'SELECT * FROM jass2019.dbo.artikli, jass2019.dbo.cenovnik '
                   f'WHERE jass2019.dbo.artikli.SIFRA=jass2019.dbo.cenovnik.SIF_ART')
    columns = [column[0] for column in cursor.description]
    table_data = dict()
    for c_name in columns:
        table_data[c_name] = []

    for row in cursor:
        arr = list(row)
        for i in range(len(arr)):
            table_data[columns[i]].append(arr[i])

    products_merged = pd.DataFrame(data=table_data)

    product_store_data = {
        'id': [],
        'price': [],
        'product_name': [],
        'warehouse_id': []
    }

    for _, row in products_merged.iterrows():
        product_store_data['id'].append(row.SIFRA)
        product_store_data['price'].append(row.CENA_P_SD)
        product_store_data['product_name'].append(row.NAZIV)
        product_store_data['warehouse_id'].append(row.SIF_MAG)

    products = pd.DataFrame(data=product_store_data)

    cursor.execute(
        f'SELECT * FROM jass2019.dbo.hed_dok, jass2019.dbo.promet WHERE jass2019.dbo.hed_dok.ID=jass2019.dbo.promet.ID')
    columns = [column[0] for column in cursor.description]
    visited = [False for _ in columns]
    mapper = dict()

    for i in range(len(columns)):
        is_visited = mapper.get(columns[i], False)
        if is_visited:
            visited[i] = True
        mapper[columns[i]] = True

    table_data = dict()
    for c_name in columns:
        table_data[c_name] = []

    for row in cursor:
        arr = list(row)
        for i in range(len(arr)):
            if (visited[i]):
                continue
            table_data[columns[i]].append(arr[i])

    store_transactions_df = pd.DataFrame(data=table_data)

    # customer_transactions = customer_transactions[customer_transactions.VKUPNO > 0]
    store_transactions_df['DAT_DOK'] = store_transactions_df['DAT_DOK'].apply(
        lambda x: pd.to_datetime(x).date().strftime('%d-%m-%Y'))
    store_transactions_df['SIF_ART'] = store_transactions_df['SIF_ART'].apply(lambda x: x.strip())
    store_transactions_df['SIF_MAG'] = store_transactions_df['SIF_MAG'].apply(lambda x: x.strip())

    c_data = {
        'date': [],
        'product_id': [],
        'store_id': [],
        'warehouse_id': [],
        'customer_id': [],
        'year': [],
        'month': [],
        'day': [],
        'product_name': [],
        'quantity': [],
        'transaction_price': [],
        'customer_name': [],
        'document_type': [],
        'employee_id': [],
        'paying_type': [],
        'time': [],
        'tax': [],
        'sale': [],
        'BR_DOK': [],
        'FAK_KOM_DOK': [],
        'BR_VL_DOK': [],
        'ID': [],
        'hour': []
    }

    def convert_date(date):
        date_list = date.split('-')
        date_list = [int(x) for x in date_list]
        return tuple(date_list)

    foo1 = products.id.unique()
    store_transactions_df['SIF_ART'] = store_transactions_df['SIF_ART']
    foo2 = store_transactions_df.SIF_ART.unique()

    mistakes = []

    for i in foo2:
        if i not in foo1:
            mistakes.append(i)

    for _, row in store_transactions_df.iterrows():
        if row.SIF_ART in mistakes:
            continue

        c_data['date'].append(row.DAT_DOK)
        c_data['store_id'].append(row.SIF_ART)
        c_data['product_id'].append(row.SIF_ART)
        c_data['warehouse_id'].append(row.SIF_MAG)
        c_data['customer_id'].append(row.SIF_MAG)
        day, month, year = convert_date(row.DAT_DOK)
        c_data['day'].append(day)
        c_data['month'].append(month)
        c_data['year'].append(year)
        curr_product = products[products.id == row.SIF_ART]
        c_data['product_name'].append(curr_product.product_name.values[0])
        c_data['quantity'].append(row.KOL_IZL if row.KOL_VL == 0 else row.KOL_VL)
        c_data['transaction_price'].append(row.VKUPNO)
        c_data['customer_name'].append(row.SIF_MAG)
        c_data['document_type'].append(row.TIP_DOK)
        c_data['employee_id'].append(row.KORISNIK)
        c_data['paying_type'].append(row.nacin_pl)
        c_data['time'].append(row.vreme)
        c_data['tax'].append(row.STAPKA)
        c_data['sale'].append(row.POPUST)
        c_data['BR_DOK'].append(row.BR_DOK)
        c_data['FAK_KOM_DOK'].append(row.FAK_KOM_DOK)
        c_data['BR_VL_DOK'].append(row.BR_VL_DOK)
        c_data['ID'].append(row.ID)
        time = str(row.vreme).split(':')
        c_data['hour'].append(time[0] if len(time) > 0 else None)

    transactions_store = pd.DataFrame(data=c_data)

    leonidas_scm = transactions_store[transactions_store.warehouse_id == '1']

    leonidas_scm = leonidas_scm[leonidas_scm.transaction_price == 2240]

    invalid_sum_ids = leonidas_scm.product_id.unique()

    accurate_transaction_prices = []

    for i, row in transactions_store.iterrows():
        if row.product_id in invalid_sum_ids:
            accurate_transaction_prices.append(float(row.transaction_price) * float(row.quantity))
        else:
            accurate_transaction_prices.append(float(row.transaction_price))

    transactions_store['transaction_price'] = accurate_transaction_prices

    return transactions_store


def create_employees_csv(cursor):
    return create_df_from_table(cursor, 'korisnici')
