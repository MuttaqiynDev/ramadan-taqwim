from dataclasses import dataclass

@dataclass(frozen=True)
class Region:
    code: str        # internal
    title: str       # UI
    api_name: str    # islomapi.uz uchun


REGIONS: list[Region] = [
    Region("Toshkent", "Toshkent", "Toshkent"),
    Region("Andijon", "Andijon", "Andijon"),
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

# Backward compatibility map if needed
REGION_MAP = {r.title: r.api_name for r in REGIONS}

def get_region_by_code(code: str) -> Region | None:
    for r in REGIONS:
        if r.code == code:
            return r
    return None
