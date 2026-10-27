# Communicate with the API using concurrent programming. The challenge is to make sure that API requests stay within the 
# rate limit of the API you're using, but that at the same time retrieving a lot of data doesn't block the applicatio (to_thread used).

import itertools
import logging, os
from dotenv import load_dotenv

import requests
import asyncio
import json
import pandas as pd
from http import HTTPStatus

from model.data import Data

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class RateLimitExceeded(Exception):
    pass

load_dotenv()
API_key = os.getenv("AGIFY_API_KEY")
if not API_key:
    raise RuntimeError("AGIFY_API_KEY not found - check your .env file")

def analyze_results(results):
    # flatten the list of results and create a DataFrame
    rows = list(itertools.chain.from_iterable(r for r in results if isinstance(r, list)))
    # print(rows) 
    
    df = pd.DataFrame(rows)
    # show rows and columns of the DataFrame in pair eg. (7,4)
    # print(df.shape)
    # print(df.columns.tolist())
    # sorted_df = df.sort_values("age", ascending=False)
    # print(sorted_df)

    # ranking the ages within each country, with 1 being the oldest
    df["age_rank"] = df.groupby("country_id")["age"].rank(ascending=False)

    # which names are the yougest in each country?
    youngest = df.loc[df.groupby("country_id")["age"].idxmin()]
    print(youngest)
    print("Names that are the youngest in each country: ", ", ".join(youngest["name"]))

    # pivoting and having now as columns the country_id and as index the name, and as values the age
    pivot_by_name = df.pivot(index="name", columns="country_id", values="age")
    # check if you have the pivot_by_name['US'] before calculating the difference
    if {'US', 'GR'}.issubset(pivot_by_name.columns):
        pivot_by_name['age_diff'] = pivot_by_name['US'] - pivot_by_name['GR']
        # print(pivot_by_name.shape)
        # print(pivot_by_name.columns.tolist())
        print(pivot_by_name)

        # which names are older in the US than in Greece, and by how much?
        mask = pivot_by_name["age_diff"] > 0          
        older_in_us = pivot_by_name[mask]             
        print("%s names are older in the US than in Greece from total of %s:" % (len(older_in_us), len(pivot_by_name)), ", ".join(older_in_us.index))

async def fetch_data(url: str, params: dict) -> dict:
    response = await asyncio.to_thread(requests.get, url, params=params, timeout=10)
    log.info("names remaining: %s", response.headers.get("x-rate-limit-remaining"))

    if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
        raise RateLimitExceeded(f"resets in {response.headers.get('x-rate-limit-reset')} s")

    response.raise_for_status()
    data = response.json()
    print("Fetched data: ", data)
    validate_data(data)
    return data


def validate_data(data) -> None:
    from model.data import Data

    try:
        if isinstance(data, list):
            for item in data:
                Data(**item)
        else:
            Data(**data)
    except Exception as e:
        log.error("Data validation error: %s", e)
        raise

def validate_countries(countries: list) -> list:
    for country in countries:
        if len(country) != 2 or not country.isalpha():
            log.warning("Removed invalid country code: %s. Input must be a 2-letter alphabetic code.", country)
            countries.remove(country)
    return countries

async def main():
    url = "https://api.agify.io"
    names = ["michael", "", "mary"]
    countries = ["USaa", "GR"]

    valid_countries = validate_countries(countries)
    print("Valid countries: ", valid_countries)

    results = await asyncio.gather(*[fetch_data(url, {"name[]": names, "apikey": API_key, "country_id": country_id}) for country_id in valid_countries], return_exceptions=True)

    serializable_results = []
    for r in results:
        if isinstance(r, RateLimitExceeded):
            log.warning("quota used up: %s", r)
            serializable_results.append({"error": type(r).__name__, "message": str(r)})
        elif isinstance(r, Exception):
            log.error("request failed: %s", type(r).__name__)
            serializable_results.append({"error": type(r).__name__, "message": str(r)})
        else:
            serializable_results.append(r)

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(serializable_results, f, indent=4)

    valid_results = [r for r in results if isinstance(r, list)]
    analyze_results(valid_results)

    # payload = data.get('data', {})    
    # pairs = [(item["alias"], item["desc"]) for item in payload]
    # print(*pairs, sep="\n\n")

if __name__ == "__main__":
    asyncio.run(main())
