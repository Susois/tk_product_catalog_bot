from dataclasses import dataclass, field


@dataclass
class Product:
    source_url: str
    resolved_url: str
    product_id: str = ""
    name: str = ""
    price: str = ""
    currency: str = "VND"
    image_urls: list[str] = field(default_factory=list)

