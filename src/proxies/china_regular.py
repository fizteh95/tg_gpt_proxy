import time
from hashlib import sha256

import aiohttp

from src.domain.models import Proxy, Context


class CustomProxy(Proxy):
    def __init__(self, url: str, password: str | None = None) -> None:
        super().__init__(url=url, password=password)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Ch-Ua": '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Linux"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        self.first_start = True

    @staticmethod
    def generate_sign(timestamp: str, content: str) -> str:
        return sha256(f"{timestamp}:{content}:".encode("utf-8")).hexdigest()

    async def generate(self, content: Context) -> str:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            if self.first_start:
                self.first_start = False
                get_urls = [
                    "https://gpt.aifree.site/",
                    "https://gpt.aifree.site/registerSW.js",
                    "https://analytics.gptnb.xyz/js/script.js",
                    "https://gpt.aifree.site/_astro/hoisted.8bdc4fc1.js",
                    "https://gpt.aifree.site/_astro/Layout.astro_astro_type_script_index_0_lang.a657d0a3.js",
                    "https://gpt.aifree.site/_astro/index.aa026a57.css",
                    "https://gpt.aifree.site/_astro/index.d51ee4b0.css",
                    "https://gpt.aifree.site/_astro/Generator.de766427.js",
                    "https://gpt.aifree.site/_astro/client.0dc58ebc.js",
                ]
                for url in get_urls:
                    async with session.get(url):
                        pass

                # auth
                auth_data = {"pass": None}
                async with session.post(
                    "https://gpt.aifree.site/api/auth",
                    json=auth_data,
                    headers=self.headers,
                ) as r:
                    print(f"{r.status}, {r.url}")
                # event
                event_data = {
                    "n": "pageview",
                    "u": "https://gpt.aifree.site/",
                    "d": "gpt.aifree.site",
                    "r": "https://github.com/LiLittleCat/awesome-free-chatgpt/blob/main/README_en.md",
                    "w": 834,
                }
                async with session.post(
                    "https://analytics.gptnb.xyz/api/event", data=event_data
                ) as r:
                    print(f"{r.status}, {r.url}")

                get_urls2 = [
                    "https://gpt.aifree.site/_astro/web.0d5d0bd9.js",
                    "https://gpt.aifree.site/icon.svg",
                    "https://gpt.aifree.site/manifest.webmanifest",
                    "https://gpt.aifree.site/pwa-192.png",
                ]
                for url in get_urls2:
                    async with session.get(url):
                        pass

            # generate
            input_text = content.messages[-1]["content"]
            timestamp = str(int(time.time() * 1000))
            sign = self.generate_sign(timestamp=timestamp, content=input_text)
            generate_data = {
                "messages": content.messages,
                "time": int(timestamp),
                "pass": None,
                "sign": sign,
            }
            async with session.post(
                "https://gpt.aifree.site/api/generate", json=generate_data
            ) as r:
                response_text = await r.text()
                return response_text
