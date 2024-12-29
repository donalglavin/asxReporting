import requests
import pandas as pd
import plotly.express as px

colors = [
    "#263238",
    "#37474f",
    "#455a64",
    "#546e7a",
    "#607d8b",
    "#78909c",
    "#90a4ae",
    "#b0bec5",
    "#cfd8dc",
    "#eceff1",
]


def asx_listings():
    """
    Function queries the ASX directly for the current list of all listed companies. This query then returns a json
    object which is converted into a pandas dataframe and returned by the function.
    """
    url = "https://asx.api.markitdigital.com/asx-research/1.0/companies/directory"

    querystring = {
        "page": "0",
        "itemsPerPage": "10000",
        "order": "ascending",
        "orderBy": "companyName",
        "includeFilterOptions": "true",
        "recentListingsOnly": "false",
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "DNT": "1",
        "Origin": "https://www.asx.com.au",
        "Referer": "https://www.asx.com.au/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    response = requests.get(url, headers=headers, params=querystring)
    try:
        response.raise_for_status()

    except requests.exceptions.HTTPError as e:
        raise ValueError("Error with request: " + str(e))

    listings = response.json()["data"]["items"]
    count = response.json()["data"]["count"]

    if len(listings) == count:
        # Format Data Appropriately before returning.
        res = pd.json_normalize(listings).convert_dtypes()
        res["dateListed"] = pd.to_datetime(res["dateListed"], format="%Y-%m-%d")
        res["marketCap"] = (pd.to_numeric(res["marketCap"], errors="coerce")).astype(
            "object"
        )
        return res
    else:
        raise ValueError("Could not read all listings")


def format(x):
    if pd.isna(x):
        return "NaN"
    elif x < 1e6:
        return "${:.0f}K".format(x / 1e3)
    elif x < 1e9 and x >= 1e6:
        return "${:.0f}M".format(x / 1e6)
    elif x < 1e12 and x >= 1e9:
        return "${:.0f}B".format(x / 1e9)


# Main function to generate report files and data.
if __name__ == "__main__":
    out = asx_listings()

    # Subset and rename columns for interpretation.
    report = out[
        [
            "symbol",
            "displayName",
            "industry",
            "priceChangeFiveDayPercent",
            "marketCap",
        ]
    ].rename(
        columns={
            "symbol": "Sym",
            "displayName": "Name",
            "industry": "Industry",
            "priceChangeFiveDayPercent": "&Delta; 5d%",
            "marketCap": "MCap ($m)",
        }
    )

    # Convert Market capital to millions.
    report.loc[:, report.columns[4]] = report[report.columns[4]].div(1e6)

    # Create the overview graphic for the ASX lsitings and market share.
    fig = px.sunburst(report, path=["Industry", "Name"], values="MCap ($m)")
    fig.update_traces(
        hovertemplate="</br>%{label}</br>$%{value:,.1f}m (%{percentEntry:.2%} share of Total) </br>%{parent} - \
        %{percentParent:.2%}"
    )
    # Return the plotly json data to be used by hugo.
    fig.write_json("data/overview.json")

    # ASX Company Directory Table.
    report.style.format(
        "{:.1f}",
        na_rep="",
        subset=[report.columns[3], report.columns[4]],
        thousands=",",
        decimal=".",
    ).set_table_styles(
        [
            {
                "selector": "tr:nth-child(even)",
                "props": f"background-color: {colors[-2]}",
            },
            {
                "selector": "tr:hover",
                "props": f"background-color: {colors[-3]}; ",
            },
            {
                "selector": "td:hover",
                "props": f"background-color: {colors[-6]}; color:{colors[-1]};",
            },
            {
                "selector": "td",
                "props": "padding: 2px 5px;",
            },
            {
                "selector": "th",
                "props": f"background-color: {colors[0]}; color:{colors[-1]}; text-align: left;",
            },
            {
                "selector": "td.col3",
                "props": "text-align: center;",
            },
            {
                "selector": "td.col4",
                "props": "text-align: right;",
            },
            {
                "selector": "th",
                "props": f"background-color: {colors[0]}; color:{colors[-1]}; padding: 2px 5px;",
            },
        ]
    ).hide().bar(
        vmin=report[report.columns[3]].min(),
        vmax=report[report.columns[3]].max(),
        cmap="RdBu",
        height=100,
        width=100,
    ).to_html(
        "data/result.html", table_id="company_directory", index=False, index_names=False
    )

    # Return json object of stock codes and listing dates.
    out[["symbol", "dateListed"]].to_json("data/syms.json")
