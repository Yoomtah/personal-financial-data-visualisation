from bokeh.models import HoverTool
from bokeh.io import curdoc
from bokeh.layouts import column,row
import pandas as pd
from statement_parser import parse_ofx_statements
import holoviews as hv

pd.options.plotting.backend = 'holoviews'
merged_df = parse_ofx_statements()


def render_basic_graphs(df, transaction_type):
    render_list = []
    df['amount'] = abs(df['amount']).astype(float)
    time_hover = HoverTool(tooltips=[("amount", "$@amount{0,0.00}"), ("date", '@date_formatted')]) 
    time_line = df.plot.line(x='date', y='amount', logy=True, yformatter='$%.00f', title=f"{transaction_type} over time").opts(tools=[time_hover])

    render_list.append(hv.render(time_line, backend='bokeh'))

    cat_hover = HoverTool(tooltips=[("amount", "$@amount{0,0.00}"), ("category", "@category")]) 
    categories_bar = df.groupby(['category'])['amount'].sum().plot.bar(x='category', y='amount',
            yformatter='$%.00f', rot=90, title=f"{transaction_type} by Category").opts(tools=[cat_hover])
    render_list.append(hv.render(categories_bar, backend="bokeh"))
    return render_list


expense_filter = merged_df['type'].str.contains("Expense")
df = merged_df[expense_filter].copy()

expense_renders = render_basic_graphs(df, "Expense")

income_filter = merged_df['type'].str.contains("Income")
income_df = merged_df[income_filter].copy()

income_renders = render_basic_graphs(income_df, "Income")



curdoc().title = "Personal Finance"
curdoc().add_root(row(column(expense_renders), column(income_renders)))
