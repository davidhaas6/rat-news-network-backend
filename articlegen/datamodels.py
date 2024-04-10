from pydantic.dataclasses import dataclass
from pydantic import TypeAdapter


@dataclass
class Article:
    article_id: str
    title: str
    body: str
    overview: str = None
    url: str = None
    img_path: str = None
    generator: str = None
    timestamp: str = None

    def from_dict(dictionary: dict):
        return TypeAdapter(Article).validate_python(dictionary)
