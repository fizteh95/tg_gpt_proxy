import asyncio
import datetime

import aiohttp

from src.domain.models import Context
from src.domain.models import Proxy


class CustomProxy(Proxy):
    def __init__(self) -> None:
        super().__init__()
        self.name = "Claude bounded"
        self.description = (
            "Зеркало Anthropic. Ограничение на количество токенов в ответе: 2048. "
            "Время ответа может быть увеличено относительно других прокси."
        )
        self.premium = True
        self.last_times: list[datetime.datetime] = []

    def _if_we_can_request(self) -> bool:
        if len(self.last_times) < 3:
            return True
        if self.last_times[0] < (
            datetime.datetime.now() - datetime.timedelta(minutes=1)
        ):
            return True
        return False

    def _update_counters(self) -> None:
        self.last_times.append(datetime.datetime.now())
        if len(self.last_times) > 3:
            self.last_times.pop(0)

    @staticmethod
    async def __generate(content: Context) -> str:
        headers = {"Authorization": "Bearer a2718fdd-9109-440b-ab53-93da03935d6f"}
        async with aiohttp.ClientSession(headers=headers) as session:
            generate_data = {
                "messages": content.messages,
                "model": "gpt-4",
                "stream": False,
                "max_tokens": 2048,
            }
            async with session.post(
                "https://thecentuaro-oai-proxy-geoblock-zov-edition.hf.space/proxy/anthropic/v1/chat/completions",
                json=generate_data,
            ) as r:
                try:
                    response_json = await r.json()
                    response_text: str = response_json["choices"][0]["message"][
                        "content"
                    ]
                    return response_text
                except Exception as e:
                    raise Exception(f"Anthropic GEO proxy error: {e}")

    async def generate(self, content: Context) -> str:
        while not self._if_we_can_request():
            await asyncio.sleep(3)
        self._update_counters()
        response = await self.__generate(content=content)
        return response
