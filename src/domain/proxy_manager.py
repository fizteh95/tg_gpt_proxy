import importlib.util
import os
import random
import sys
import typing as tp
from pathlib import Path

from src.domain.models import Proxy
from src.services.message_bus import MessageBus
from src.services.unit_of_work import AbstractUnitOfWork


def load_so_module(module_name: str) -> tp.Any:
    # module_name_without_so = module_name.replace(".so", "")
    # file_path = Path(f"so/{module_name_without_so}.so")
    # spec = importlib.util.spec_from_file_location(module_name_without_so, file_path)
    # module = importlib.util.module_from_spec(spec)  # type: ignore
    # sys.modules[module_name_without_so] = module
    # spec.loader.exec_module(module)  # type: ignore
    module_name_without_py = module_name.replace(".py", "")
    file_path = Path(f"src/proxies/{module_name_without_py}.py")
    spec = importlib.util.spec_from_file_location(module_name_without_py, file_path)
    module = importlib.util.module_from_spec(spec)  # type: ignore
    sys.modules[module_name_without_py] = module
    spec.loader.exec_module(module)  # type: ignore
    return module


class ProxyManager:
    def __init__(self, uow: AbstractUnitOfWork, bus: MessageBus) -> None:
        self.uow = uow
        self.bus = bus
        self.proxies: dict[str, Proxy] = {}
        self.proxy_status: dict[str, bool] = {}

        # download proxies
        # filenames: list[str] = next(os.walk("./so/"), (None, None, []))[2]  # type: ignore
        filenames: list[str] = next(os.walk("./src/proxies/"), (None, None, []))[2]  # type: ignore
        for name in filenames:
            if name == "__init__.py":
                continue
            module = load_so_module(name)
            proxy = module.CustomProxy()
            self.proxies[proxy.name] = proxy
            self.proxy_status[proxy.name] = False

    async def get_proxy_properties(
        self, only_working: bool = False
    ) -> list[dict[str, str | bool]]:
        proxies: list[dict[str, str | bool]] = []
        for proxy_name, proxy in self.proxies.items():
            if not self.proxy_status.get(proxy_name) and only_working:
                continue
            proxies.append(
                {
                    "name": proxy.name,
                    "description": proxy.description,
                    "premium": proxy.premium,
                }
            )
        return proxies

    async def get_proxy_instances(self) -> list[Proxy]:
        return list(self.proxies.values())

    async def make_proxy_working(self, proxy: Proxy) -> None:
        self.proxy_status[proxy.name] = True

    async def make_proxy_not_working(self, proxy: Proxy) -> None:
        self.proxy_status[proxy.name] = False

    async def get_proxy_by_name(self, name: str) -> Proxy | None:
        return self.proxies.get(name)

    async def get_default_proxy(self) -> Proxy:
        for proxy_name, proxy in self.proxies.items():
            if self.proxy_status[proxy_name] and not proxy.premium:
                return proxy
        else:
            return random.choice(list(self.proxies.values()))
