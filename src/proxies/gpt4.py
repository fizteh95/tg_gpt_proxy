import aiohttp

from src.domain.models import Context
from src.domain.models import Proxy


class CustomProxy(Proxy):
    def __init__(self) -> None:
        super().__init__()
        self.name = "ChatGPT-3.5 bounded"
        self.description = (
            "Зеркало OpenAI. Ограничение на количество токенов в ответе: 200."
        )

    async def generate(self, content: Context) -> str:
        headers = {"Authorization": "Bearer 54a0a1be-b0ac-4d0e-ac0f-a0e3c40def6d"}
        async with aiohttp.ClientSession(headers=headers) as session:  # headers=headers
            generate_data = {
                "messages": content.messages,
                "model": "gpt-4",  # "gpt-3.5-turbo",
                "stream": False,
                "max_tokens": 1200,
            }
            async with session.post(
                # https://thecentuaro-oai-proxy-geoblock-zov-edition.hf.space/proxy/anthropic
                "https://thecentuaro-oai-proxy-geoblock-zov-edition.hf.space/proxy/openai/chat/completions",
                json=generate_data,
            ) as r:
                try:
                    response_json = await r.json()
                    print(response_json)
                    response_text: str = response_json["choices"][0]["message"]["content"]
                    return response_text
                except:
                    print(response_json)


"""
import asyncio
from src.domain.models import Context
from src.proxies.anthropic import CustomProxy

p = CustomProxy()
c = Context(messages=[{"role": "user", "content": "Привет! Кто ты?"}])

async def gen():
    res = await p.generate(content=c)
    print(res)
    
asyncio.run(gen())
"""