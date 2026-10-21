from typing import Iterable, List
from pathlib import Path
from app.models.domain.taint_path import TaintPath  
from app.config.settings import settings


# Создаем путь для сохранения созданного файла
def save_taint_paths(paths: Iterable[TaintPath]):
    out_path = settings.taint_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0

    with open(out_path, "w", encoding="utf-8") as f:
        for tp in paths:
            f.write(tp.model_dump_json() + "\n") 
            n+=1
    return n

# Выгружаем файл для чтения
def load_taint_path(path: Path) -> List[TaintPath]:
    with open(path, "r", encoding="utf-8") as f:
        return [TaintPath.model_validate_json(line) for line in f if line.strip()]


