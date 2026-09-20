from enum import StrEnum


class LegalRegime(StrEnum):
    BY_PRODUCT = "by_product"
    SECONDARY_RAW = "secondary_raw"
    USED_MATERIAL = "used_material"
    WASTE = "waste"
