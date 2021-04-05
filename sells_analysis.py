import pandas as pd
import datetime
import streamlit as st
import plotly.express as px
import numpy as np

def convert_date(date):
    curr_date = date.strftime("%d-%m-%Y")
    values = curr_date.split('-')
    return datetime.datetime(int(values[2]), int(values[1]), int(values[0]))


def most_profitable_products(df):
    product_names = {arr[0]: arr[1] for arr in df[['product_id', 'product_name']].values}
    df = df.groupby('product_id')['transaction_price'].sum().sort_values(ascending=False)

    p_data = []
    for p_id, p_sum in df.items():
        p_name = product_names[p_id]
        p_data.append([p_name, p_sum])

    df = pd.DataFrame(data=p_data, columns=['product', 'sells'])

    return df


def daily_profits(logona_data, leonidas_data):
    daily_profits_logona = logona_data.groupby('p_date')['transaction_price'].sum().sort_index()
    daily_profits_leonidas = leonidas_data.groupby('p_date')['transaction_price'].sum().sort_index()

    curr_data = []

    for (day, logona_profit), (_, leondas_profit) in zip(daily_profits_logona.items(), daily_profits_leonidas.items()):
        curr_data.append([day, logona_profit, 'Logona'])
        curr_data.append([day, leondas_profit, 'Leonidas'])

    return pd.DataFrame(data=curr_data, columns=['day', 'profit', 'store'])


def hourly_sale_distribution(df):
    df = df.hour.value_counts()
    temp_data = [[h, v] for h, v in df.items() if h is not None]
    df = pd.DataFrame(data=temp_data, columns=['hour', 'sells'])
    df = df.sort_values(by='hour')
    return df


# data = pd.read_csv('transaction_store.csv')
# data['p_date'] = [datetime.datetime(d[0], d[1], d[2]) for d in data[['year', 'month', 'day']].values]
#
# data = data.sort_values(by='p_date').reset_index(drop=True)

def sells_analysis(data):
    data = data.copy()

    data['p_date'] = [datetime.datetime(d[0], d[1], d[2]) for d in data[['year', 'month', 'day']].values]

    data = data.sort_values(by='p_date').reset_index(drop=True)
    # Gloabl profits

    global_daily_profits_df = data[data.document_type == '02'].reset_index(drop=True)

    global_profits = daily_profits(
        global_daily_profits_df[global_daily_profits_df.warehouse_id == '3'].reset_index(drop=True),
        global_daily_profits_df[global_daily_profits_df.warehouse_id == '5'].reset_index(drop=True))

    gp_logona = global_profits[global_profits.store == 'Logona'].reset_index(drop=True)
    gp_leonidas = global_profits[global_profits.store == 'Leonidas'].reset_index(drop=True)

    gp_logona['ma30'] = gp_logona.iloc[:, 1].rolling(window=30).mean()
    gp_leonidas['ma30'] = gp_leonidas.iloc[:, 1].rolling(window=30).mean()

    global_profits = pd.concat([gp_logona, gp_leonidas]).reset_index(drop=True)
    global_profits = global_profits.sort_values(by='day').reset_index(drop=True)
    global_profits = global_profits.dropna()

    global_profits_fig = px.line(global_profits, x="day", y="ma30", color='store')
    global_profits_fig.update_layout({'xaxis': {'title': 'Ден'},
                                      'yaxis': {'title': 'Промет'}
                                      })

    st.header(f'Просечен месечен промет')
    st.plotly_chart(global_profits_fig, use_column_width=True)

    # Analysis in a given range
    st.header('Анализа на продажби во избран временски период')

    max_date = datetime.date.today()
    min_date = max_date - datetime.timedelta(10)

    date_range = st.date_input("Избери интервал за анализа", (min_date, max_date))

    if len(date_range) == 1:
        return None

    start_date = convert_date(date_range[0])
    end_date = convert_date(date_range[1])

    filtered_date = data[(data.p_date >= start_date) & (data.p_date <= end_date)].reset_index(drop=True)
    filtered_date = filtered_date[filtered_date.document_type == '02'].reset_index(drop=True)
    #
    # leonidas_data = data[data.warehouse_id == '05'].reset_index(drop=True)
    # logona_data = data[data.warehouse_id == '03'].reset_index(drop=True)

    leonidas_data = filtered_date[filtered_date.warehouse_id == '5'].reset_index(drop=True)
    logona_data = filtered_date[filtered_date.warehouse_id == '3'].reset_index(drop=True)

    # Most profitable producs
    NUMBER_OF_TOP_PRODUCTS = 10

    logona_most_profits = most_profitable_products(logona_data)
    leonidas_most_profits = most_profitable_products(leonidas_data)

    logona_most_profits['store'] = 'Logona'
    leonidas_most_profits['store'] = 'Leonidas'
    grouped_most_profits = pd.concat([logona_most_profits.head(NUMBER_OF_TOP_PRODUCTS),
                                      leonidas_most_profits.head(NUMBER_OF_TOP_PRODUCTS)]).reset_index(drop=True)

    grouped_most_profits_fig = px.bar(grouped_most_profits, x='product', y='sells', color='store', barmode='group')
    grouped_most_profits_fig.update_layout({'xaxis': {'title': 'Продукти'},
                                            'yaxis': {'title': 'Промет'}
                                            })

    st.header(f'Најпрофитабилни {NUMBER_OF_TOP_PRODUCTS} продукти')
    st.plotly_chart(grouped_most_profits_fig, use_column_width=True)

    # Daily profits

    profits = daily_profits(logona_data, leonidas_data)
    daily_profits_fig = px.line(profits, x="day", y="profit", color='store')
    daily_profits_fig.update_layout({'xaxis': {'title': 'Ден'},
                                     'yaxis': {'title': 'Промет'}
                                     })

    st.header(f'Профит на ден')
    st.plotly_chart(daily_profits_fig, use_column_width=True)

    # Hourly sells
    hours_distb = hourly_sale_distribution(filtered_date)
    hours_fig = px.bar(hours_distb, x='hour', y='sells')
    hours_fig.update_layout({'xaxis': {'title': 'Саат'},
                             'yaxis': {'title': 'Број на продажби'}
                             })

    st.header(f'Најфреквентни саати')
    st.plotly_chart(hours_fig, use_column_width=True)

    # All sales
    logona_details = logona_data.groupby('product_name')[['transaction_price', 'quantity']].sum() \
        .sort_values(by='transaction_price', ascending=False)
    logona_details['transaction_price'] = logona_details['transaction_price'].astype(np.int)

    leonidas_details = leonidas_data.groupby('product_name')[['transaction_price', 'quantity']].sum() \
        .sort_values(by='transaction_price', ascending=False)
    leonidas_details['transaction_price'] = leonidas_details['transaction_price'].astype(np.int)

    cols = st.beta_columns(3)
    cols[0].subheader('Најпрофитабилни продукти во Логона')
    cols[0].table(logona_details)

    cols[2].subheader('Најпрофитабилни продукти во Леонидас')
    cols[2].table(leonidas_details)
