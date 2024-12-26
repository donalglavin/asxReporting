import requests
import pandas as pd


def run():
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
        res["marketCap"] = pd.to_numeric(res["marketCap"], errors="coerce").astype(
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


if __name__ == "__main__":
    out = run()
    report = out[
        ["symbol", "displayName", "industry", "marketCap", "priceChangeFiveDayPercent"]
    ].sort_values(by="marketCap", ascending=False)

    report.loc[:, "priceChangeFiveDayPercent"] = report[
        "priceChangeFiveDayPercent"
    ].round(2)
    report.loc[:, "marketCap"] = report["marketCap"].apply(format)

    report.columns = [
        "Sym",
        "Name",
        "Industry",
        "M Cap",
        "%5d",
    ]
    report.to_csv("./data/company_directory.csv", index=False)
