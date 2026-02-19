from dataclasses import dataclass

@dataclass(frozen=True)
class Region:
    code: str
    title: str
    api_name: str


REGIONS: list[Region] = [
    Region("Toshkent", "Toshkent", "Toshkent"),
    Region("Andijan", "Andijan", "Andijan"),
    Region("Buxoro", "Buxoro", "Buxoro"),
    Region("Farg‘ona", "Farg'ona", "Farg'ona"),
    Region("Jizzax", "Jizzax", "Jizzax"),
    Region("Xorazm", "Xorazm", "Urganch"),
    Region("Namangan", "Namangan", "Namangan"),
    Region("Navoiy", "Navoiy", "Navoiy"),
    Region("Qashqadaryo", "Qashqadaryo", "Qarshi"),
    Region("Samarqand", "Samarqand", "Samarqand"),
    Region("Sirdaryo", "Sirdaryo", "Guliston"),
    Region("Surxondaryo", "Surxondaryo", "Termiz"),
    Region("Qoraqalpog‘iston", "Qoraqalpog‘iston", "Nukus"),
]

REGION_MAP = {r.title: r.api_name for r in REGIONS}

def get_region_by_code(code: str) -> Region | None:
    for r in REGIONS:
        if r.code == code:
            return r
    return None
