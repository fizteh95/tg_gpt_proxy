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
        headers = {"Authorization": "Bearer i_love_cunny"}
        async with aiohttp.ClientSession(headers=headers) as session:
            generate_data = {
                "messages": content.messages,
                "model": "gpt-3.5-turbo",
                "stream": False,
                "max_tokens": 1200,
            }
            async with session.post(
                "https://cuteanya-cuteproxy.hf.space/proxy/openai/chat/completions",
                json=generate_data,
            ) as r:
                response_json = await r.json()
                response_text: str = response_json["choices"][0]["message"]["content"]
                return response_text
