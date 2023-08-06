from dataclasses import dataclass

import aiohttp

# from src.domain.models import Context
# from src.domain.models import Proxy


@dataclass
class Context:
    messages: list[dict[str, str]]


class CustomProxy:  # (Proxy)
    def __init__(self) -> None:
        super().__init__()
        self.name = "ChatGPT-3.5 bounded"
        self.description = (
            "Зеркало OpenAI. Ограничение на количество токенов в ответе: 200."
        )

    async def generate(self, content: Context, token: str) -> str:
        headers = {"Authorization": f"Bearer {token}"}
        async with aiohttp.ClientSession(headers=headers) as session:  # headers=headers
            generate_data = {
                "messages": content.messages,
                "model": "claude",  # "gpt-3.5-turbo",
                "stream": False,
                "max_tokens": 1200,
            }
            async with session.post(
                # "https://masutxrxd-masutxrxd.hf.space/proxy/anthropic/v1/chat/completions",
                "https://testingcodehere-oai-proxy.hf.space/proxy/openai/chat/completions",
                json=generate_data,
            ) as r:
                try:
                    response_json = await r.json()
                    print(response_json)
                    response_text: str = response_json["choices"][0]["message"][
                        "content"
                    ]
                    return response_text
                except:
                    print(response_json)


import asyncio


p = CustomProxy()
c = Context(messages=[{"role": "user", "content": "Привет! Кто ты?"}])


async def gen():
    for i in [
        "icarus410",
        "Icarus410",
        "ikarus410",
        "Ikarus410",
        "ПАЗИК",
        "Икарус410",
        "икарус410",
        "ИКАРУС410",
        "IKARUS410",
        "ICARUS410",
        "LiAZ-5256",
        "softsign",
        "fart",
        "swrslt",
        "SWRSLT",
        "SWR/SLT"
    ]:
        res = await p.generate(content=c, token=i)
        print(i)
        print(res)


asyncio.run(gen())
