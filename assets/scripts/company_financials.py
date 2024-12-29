# A script to retrieve all of the company financials for a given ASX company.
import pandas as pd
import yfinance as yf  # type: ignore

import plotly.graph_objects as go
from plotly.subplots import make_subplots

SYMS_PATH = "./data/syms.json"


def get_financials(syms):
    syms = pd.read_json(syms)
    syms["symbol"] = syms.loc[:, "symbol"].apply(lambda x: x + ".AX")

    return syms


if __name__ == "__main__":
    out = get_financials(SYMS_PATH)
    print(out.head())

    for ind, row in out.iterrows():
        sym = row["symbol"]
        tic = yf.Ticker(sym)
        hist = pd.DataFrame(tic.history(period="max"))
        hist.to_json(f"data/histories/{sym}_hist.json")

        candlesticks = go.Candlestick(
            x=hist.index,
            open=hist["Open"],
            high=hist["High"],
            low=hist["Low"],
            close=hist["Close"],
            showlegend=False,
        )

        volumebars = go.Bar(
            x=hist.index,
            y=hist["Volume"],
            showlegend=False,
        )

        fig = go.Figure(candlesticks)
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(candlesticks, secondary_y=True)
        fig.add_trace(volumebars, secondary_y=False)
        fig.update_yaxes(title="Price $", secondary_y=True, showgrid=True)
        fig.update_yaxes(title="Volume $", secondary_y=False, showgrid=False)

        # Save the plot
        fig.write_json(f"data/histories/{sym}_plot.json")

        print(f"up to {ind} of {len(out.index)}")
