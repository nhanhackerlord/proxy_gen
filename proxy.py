import aiohttp
import asyncio
import requests
from bs4 import BeautifulSoup
import os

# Proxy sources
proxy_sources = [
    "https://www.sslproxies.org/",
    "https://www.us-proxy.org/",
    "https://www.proxy-list.download/api/v1/get?type=https"
]

# Fetch proxies from a URL
def fetch_proxies(url):
    proxies = set()
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        for row in soup.find_all('tr'):
            columns = row.find_all('td')
            if len(columns) > 1:
                ip = columns[0].text.strip()
                port = columns[1].text.strip()
                proxies.add(f"http://{ip}:{port}")
    except Exception as e:
        print(f"Error fetching proxies from {url}: {e}")
    return proxies

# Check if a proxy is live
async def check_proxy(session, proxy):
    try:
        async with session.get("http://www.google.com", proxy=proxy, timeout=5) as response:
            if response.status == 200:
                return proxy
    except:
        pass
    return None

# Generate and verify proxies, appending new ones to the file
async def generate_and_verify_proxies(proxy_sources, live_proxy_file):
    while True:
        all_proxies = set()
        for source in proxy_sources:
            all_proxies.update(fetch_proxies(source))

        print(f"Fetched {len(all_proxies)} proxies. Verifying...")

        live_proxies = set()
        
        async with aiohttp.ClientSession() as session:
            tasks = [check_proxy(session, proxy) for proxy in all_proxies]
            results = await asyncio.gather(*tasks)
            for proxy in results:
                if proxy:
                    live_proxies.add(proxy)
        
        # Load current proxies from file (if exists)
        if os.path.exists(live_proxy_file):
            with open(live_proxy_file, 'r') as f:
                current_proxies = set(f.read().splitlines())
        else:
            current_proxies = set()

        # Identify new proxies that are not already in the file
        new_proxies = live_proxies - current_proxies

        # Append new live proxies to the file
        if new_proxies:
            with open(live_proxy_file, 'a') as f:  # 'a' for append mode
                for proxy in new_proxies:
                    f.write(proxy + '\n')
            print(f"Appended {len(new_proxies)} new live proxies to {live_proxy_file}")

        await asyncio.sleep(60)  # Adjust the interval for checking proxies

if __name__ == '__main__':
    live_proxy_file = 'proxy_live.txt'
    asyncio.run(generate_and_verify_proxies(proxy_sources, live_proxy_file))
