import importlib.util
import sys
from pathlib import Path
import typing as tp


def load_so_module(module_name: str) -> tp.Any:
    module_name_without_so = module_name.replace(".so", "")
    file_path = Path(f"so/{module_name_without_so}.so")
    spec = importlib.util.spec_from_file_location(module_name_without_so, file_path)
    module = importlib.util.module_from_spec(spec)  # type: ignore
    sys.modules[module_name_without_so] = module
    spec.loader.exec_module(module)  # type: ignore
    return module
