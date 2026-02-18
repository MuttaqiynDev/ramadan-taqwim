import aiohttp
import asyncio
from datetime import date

async def main():
    async with aiohttp.ClientSession() as session:
        # Check Daily for Andijon
        url = "https://islomapi.uz/api/daily"
        params = {"region": "Andijon shahri", "month": str(date.today().month), "day": str(date.today().day)}
        print(f"Requesting {url} with params {params}")
        async with session.get(url, params=params) as resp:
            print(f"Status: {resp.status}")
            try:
                data = await resp.json(content_type=None)
                print(f"Data type: {type(data)}")
                print(f"Data: {data}")
            except Exception as e:
                print(f"Error decoding JSON: {e}")
                text = await resp.text()
                print(f"Raw text: {text}")

        # Check Monthly
        url_monthly = "https://islomapi.uz/api/monthly"
        params_monthly = {"region": "Andijon", "month": str(date.today().month)}
        print(f"\nRequesting {url_monthly} with params {params_monthly}")
        async with session.get(url_monthly, params=params_monthly) as resp:
            print(f"Status: {resp.status}")
            try:
                data = await resp.json(content_type=None)
                print(f"Data type: {type(data)}")
                print(f"Data length: {len(data) if isinstance(data, list) else 'N/A'}")
                print(f"First item: {data[0] if isinstance(data, list) and data else data}")
            except Exception as e:
                print(f"Error decoding JSON (Monthly): {e}")
                text = await resp.text()
                print(f"Raw text: {text}")

if __name__ == "__main__":
    asyncio.run(main())
