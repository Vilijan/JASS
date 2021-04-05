from data_repository import retrieve_db_data
import streamlit as st
import datetime


def daily_transactions(data):

    date = st.date_input("Продажби на ден: ", )
    date = date.strftime("%d-%m-%Y")

    today_transactions = data[(data.date == date) &
                              (data.document_type == '02') &
                              (data.transaction_price > 0)].reset_index(drop=True)

    today_transactions['time'] = today_transactions['time'].astype(str)

    today_leonidas = today_transactions[today_transactions.warehouse_id == '5'].reset_index(drop=True)
    today_logona = today_transactions[today_transactions.warehouse_id == '3'].reset_index(drop=True)

    daily_sum = today_transactions.transaction_price.sum()
    daily_unique_transactions = len(today_transactions.BR_DOK.unique())
    st.header(f'Вкупно {daily_unique_transactions} продажби и {int(daily_sum)} промет во денари')
    st.header(
        f'Леонидас: {int(today_leonidas.transaction_price.sum())} Логона: {int(today_logona.transaction_price.sum())} денари')

    for i, transaction_id in enumerate(today_transactions.BR_DOK.unique()):
        single_transaction = today_transactions[today_transactions.BR_DOK == transaction_id].reset_index(drop=True)
        transaction_sum = single_transaction.transaction_price.sum()
        st.subheader(f'Продажба {i + 1}')
        cols = st.beta_columns(3)
        cols[0].subheader(f'{single_transaction.time.values[0].strip()}')
        cols[1].subheader(f'{single_transaction.employee_name.values[0]}')
        cols[2].subheader(f'{int(transaction_sum)} денари')

        display_df = single_transaction[['product_name', 'quantity', 'transaction_price']]
        display_df.columns = ['Име на продукт', 'Количина', 'Цена']

        st.table(display_df)
