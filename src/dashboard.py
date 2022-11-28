from bokeh.models import HoverTool
from bokeh.io import curdoc
from bokeh.layouts import column,row
import pandas as pd
from statement_parser import parse_ofx_statements
import holoviews as hv
from bokeh.models.formatters import DatetimeTickFormatter

pd.options.plotting.backend = 'holoviews'
merged_df = parse_ofx_statements()


def extract_month_year(date):
    return f"{date.month_name()}, {date.year}"


def render_basic_graphs(df, transaction_type):
    render_list = []
    df['amount'] = abs(df['amount']).astype(float)
    time_hover = HoverTool(tooltips=[("amount", "$@amount{0,0.00}"), ("date", '@date_formatted')]) 
    time_line = df.plot.line(x='date', y='amount', logy=True, yformatter='$%.00f', title=f"{transaction_type} over time (Log scale)").opts(tools=[time_hover])

    render_list.append(hv.render(time_line, backend='bokeh'))

    cat_hover = HoverTool(tooltips=[("amount", "$@amount{0,0.00}"), ("category", "@category")]) 
    categories_bar = df.groupby(['category'])['amount'].sum().plot.bar(x='category', y='amount',
            yformatter='$%.00f', rot=90, title=f"{transaction_type} by Category").opts(tools=[cat_hover],
            color='category', cmap='Category10')
    render_list.append(hv.render(categories_bar, backend="bokeh"))
    return render_list


def render_advanced_graphs(df, transaction_type):
    render_list = []
    df['amount'] = abs(df['amount']).astype(float)
    cat_hover = HoverTool(tooltips=[("amount", "$@amount{0,0.00}"), ("category", "@category")]) 
    df.set_index(pd.DatetimeIndex(df['date']), inplace=True)
    df = df.groupby([pd.Grouper(freq='M'), 'category'])['amount'].sum()
    formatter = DatetimeTickFormatter(days="%d-%b-%Y", months='%m/%Y', years='%m/%Y')
    stacked_bar = df.plot.bar(stacked=True, xformatter=formatter, yformatter='$%.00f', 
            title=f"{transaction_type} per Category by Month").opts(tools=[cat_hover])
    render_list.append(hv.render(stacked_bar, backend='bokeh'))

    time_hover = HoverTool(tooltips=[("amount", "$@amount{0,0.00}"), ("date", '@date_formatted')]) 
    time_line = df.plot.line(x='date', y='amount', by='category', logy=True, yformatter='$%.00f', title=f"{transaction_type} by category over time (Log scale)").opts(tools=[time_hover])

    return render_list

def render_income_vs_expense_graphs(df):
    render_list = []
    df['amount'] = abs(df['amount']).astype(float)

    time_hover = HoverTool(tooltips=[("amount", "$@amount{0,0.00}"), ("date", '@date_formatted')]) 
    time_line = df.plot.line(x='date', y='amount', by='type', yformatter='$%.00f',
            title="Income vs Expenses over time").opts(tools=[time_hover])

    render_list.append(hv.render(time_line, backend='bokeh'))

    cat_hover = HoverTool(tooltips=[("amount", "$@amount{0,0.00}"), ("type", "@type")]) 
    df.set_index(pd.DatetimeIndex(df['date']), inplace=True)
    df = df.groupby([pd.Grouper(freq='M'), 'type'])['amount'].sum()
    df.to_csv("temp.csv")
    df3 = pd.read_csv("temp.csv")
    diff_series = df3.groupby(['date'])['amount'].diff().dropna().reset_index(drop=True)
    date_series = df3['date'].drop_duplicates().reset_index(drop=True)
    diff_series = pd.DataFrame(diff_series)
    df4 = diff_series.join(date_series)
    df4['type'] = 'Surplus'
    dtformat = '%Y-%m-%d'
    df4['date'] = pd.to_datetime(df4['date'], format=dtformat)
    df4.set_index([pd.DatetimeIndex(df4['date']), 'type'], inplace=True)
    df4 = df4.drop(['date'], axis=1)
    df = pd.DataFrame(df)
    df_merged = pd.concat([df, df4])
    formatter = DatetimeTickFormatter(days="%d-%b-%Y", months='%m/%Y', years='%m/%Y')
    stacked_bar = df_merged.plot.bar(stacked=True, xformatter=formatter, yformatter='$%.00f', 
            title="Income vs Expenses by Month").opts(tools=[cat_hover])
    render_list.append(hv.render(stacked_bar, backend='bokeh'))
    return render_list


expense_filter = merged_df['type'].str.contains("Expense")
expense_df = merged_df[expense_filter].copy()

expense_renders = render_basic_graphs(expense_df, "Expense")
expense_renders += render_advanced_graphs(expense_df, "Expense")

income_filter = merged_df['type'].str.contains("Income")
income_df = merged_df[income_filter].copy()

income_renders = render_basic_graphs(income_df, "Income")
income_renders += render_advanced_graphs(income_df, "Income")


curdoc().title = "Personal Finance"
curdoc().add_root(row(column(expense_renders), column(income_renders)))
curdoc().add_root(row(render_income_vs_expense_graphs(merged_df)))
