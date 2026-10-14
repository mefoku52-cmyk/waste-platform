"""company_pages domain enums."""

from enum import StrEnum


class CompanyPageStatus(StrEnum):
    """Stav publikovania verejnej firemnej stránky.

    * ``draft`` — rozpracovaná / stiahnutá, verejne NEprístupná.
    * ``published`` — firma ju výslovne zverejnila, verejne prístupná.

    Prepnutie ``published -> draft`` = odpublikovanie (stránka prestane
    byť verejná, dáta ostávajú zachované).
    """

    DRAFT = "draft"
    PUBLISHED = "published"
