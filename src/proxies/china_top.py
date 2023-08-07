import base64
import json
import time
from hashlib import sha256

import aiohttp

from src.domain.models import Context
from src.domain.models import Proxy


class CustomProxy(Proxy):
    def __init__(self) -> None:
        super().__init__()
        self.name = "ChatGPT-3.5 #2"
        self.description = "Зеркало OpenAI #2"
        self.premium = True
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Ch-Ua": '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Linux"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Version": "1.0",
            ":Authority": "api.powerchat.top",
            "Origin": "https://powerchat.top",
            "Referer": "https://powerchat.top/",
        }
        self.first_start = True

    @staticmethod
    def generate_sign(timestamp: str) -> str:
        magic = "contact_me_to_work_together_hello@promptboom.com"
        m = sha256()
        m.update(f"{timestamp}:question:{magic}".encode("utf-8"))
        sign = m.hexdigest()
        return sign

    async def generate(self, content: Context) -> str:
        async with aiohttp.ClientSession(
            headers=self.headers
        ) as session:  # headers=self.headers
            if self.first_start:
                self.first_start = False
                get_urls = [
                    "https://powerchat.top/",
                    "https://powerchat.top/js/chunk-vendors.d2953edb.js",
                    "https://powerchat.top/js/app.73d68ff0.js",
                    "https://powerchat.top/css/chunk-vendors.88764c8a.css",
                    "https://powerchat.top/fonts/materialdesignicons-webfont.68358e87.woff2",
                    "https://powerchat.top/cdn-cgi/challenge-platform/scripts/invisible.js",
                    "https://powerchat.top/img/P.9433d061.png",
                    "https://powerchat.top/cdn-cgi/challenge-platform/h/g/scripts/jsd/74ac0d47/invisible.js",
                    "https://powerchat.top/cdn-cgi/challenge-platform/h/g/cv/result/7f294e2f5a8e9201",
                    "https://powerchat.top/favicon.ico",
                ]
                for url in get_urls:
                    async with session.get(url):
                        pass

            # generate
            timestamp = str(int(time.time() * 1000))
            sign = self.generate_sign(timestamp=timestamp)
            generate_data = {
                "did": "badf5ee8382f536d45fc26c78298a2ce",
                "chatList": content.messages,
                "special": {
                    "time": int(timestamp),
                    "sign": sign,
                    "referer": "no-referer",
                    "path": "https://powerchat.top/",
                },
            }

            json_dumped = json.dumps(generate_data)
            utf_encoded = json_dumped.encode("utf-8")
            encoded_data = base64.b64encode(utf_encoded)
            async with session.post(
                "https://api.powerchat.top/requestPowerChat",
                json={"data": encoded_data.decode()},
            ) as r:
                response_text = await r.text()
                return response_text
