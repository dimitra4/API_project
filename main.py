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

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

class RateLimitExceeded(Exception):
    pass

load_dotenv()
API_key = os.getenv("AGIFY_API_KEY")
if not API_key:
    raise RuntimeError("AGIFY_API_KEY not found - check your .env file")

async def fetch_data(url: str, params: dict) -> dict:
    response = await asyncio.to_thread(requests.get, url, params=params, timeout=10)
    log.info("names remaining: %s", response.headers.get("x-rate-limit-remaining"))
    if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
        raise RateLimitExceeded(f"resets in {response.headers.get('x-rate-limit-reset')} s")
    response.raise_for_status()
    return response.json()
   

async def main():
    url = "https://api.agify.io"
    names = ["michael", "john", "dimitra", "mary", "robert", "linda", "william"]
    country_id = "GR"

    results = await asyncio.gather(*[fetch_data(url, {"name[]": name, "apikey": API_key, "country_id": country_id}) for name in names], return_exceptions=True)
    print(type(results))
    for r in results:
        if isinstance(r, RateLimitExceeded):
            log.warning("quota used up: %s", r)
        elif isinstance(r, Exception):
            log.error("request failed: %s", type(r).__name__)

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    # flatten the list of results and create a DataFrame
    rows = list(itertools.chain.from_iterable(r for r in results if isinstance(r, list)))
    print(rows) 
    
    df = pd.DataFrame(rows)
    # show rows and columns of the DataFrame in pair eg. (7,4)
    print(df.shape)
    print(df.columns.tolist())
    sorted_df = df.sort_values("age", ascending=False)
    print(df)
    print(sorted_df)
    
    # payload = data.get('data', {})    
    # pairs = [(item["alias"], item["desc"]) for item in payload]
    # print(*pairs, sep="\n\n")

if __name__ == "__main__":
    asyncio.run(main())
