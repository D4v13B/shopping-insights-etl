"""Datos de referencia: fuente única del mapeo estado -> código USPS -> región del Census."""

from typing import Final

NORTHEAST: Final = "Northeast"
MIDWEST: Final = "Midwest"
SOUTH: Final = "South"
WEST: Final = "West"

US_STATES: Final[dict[str, tuple[str, str]]] = {
    "Alabama": ("AL", SOUTH),
    "Alaska": ("AK", WEST),
    "Arizona": ("AZ", WEST),
    "Arkansas": ("AR", SOUTH),
    "California": ("CA", WEST),
    "Colorado": ("CO", WEST),
    "Connecticut": ("CT", NORTHEAST),
    "Delaware": ("DE", SOUTH),
    "Florida": ("FL", SOUTH),
    "Georgia": ("GA", SOUTH),
    "Hawaii": ("HI", WEST),
    "Idaho": ("ID", WEST),
    "Illinois": ("IL", MIDWEST),
    "Indiana": ("IN", MIDWEST),
    "Iowa": ("IA", MIDWEST),
    "Kansas": ("KS", MIDWEST),
    "Kentucky": ("KY", SOUTH),
    "Louisiana": ("LA", SOUTH),
    "Maine": ("ME", NORTHEAST),
    "Maryland": ("MD", SOUTH),
    "Massachusetts": ("MA", NORTHEAST),
    "Michigan": ("MI", MIDWEST),
    "Minnesota": ("MN", MIDWEST),
    "Mississippi": ("MS", SOUTH),
    "Missouri": ("MO", MIDWEST),
    "Montana": ("MT", WEST),
    "Nebraska": ("NE", MIDWEST),
    "Nevada": ("NV", WEST),
    "New Hampshire": ("NH", NORTHEAST),
    "New Jersey": ("NJ", NORTHEAST),
    "New Mexico": ("NM", WEST),
    "New York": ("NY", NORTHEAST),
    "North Carolina": ("NC", SOUTH),
    "North Dakota": ("ND", MIDWEST),
    "Ohio": ("OH", MIDWEST),
    "Oklahoma": ("OK", SOUTH),
    "Oregon": ("OR", WEST),
    "Pennsylvania": ("PA", NORTHEAST),
    "Rhode Island": ("RI", NORTHEAST),
    "South Carolina": ("SC", SOUTH),
    "South Dakota": ("SD", MIDWEST),
    "Tennessee": ("TN", SOUTH),
    "Texas": ("TX", SOUTH),
    "Utah": ("UT", WEST),
    "Vermont": ("VT", NORTHEAST),
    "Virginia": ("VA", SOUTH),
    "Washington": ("WA", WEST),
    "West Virginia": ("WV", SOUTH),
    "Wisconsin": ("WI", MIDWEST),
    "Wyoming": ("WY", WEST),
}

GENDERS: Final = ("Male", "Female")
SEASONS: Final = ("Winter", "Spring", "Summer", "Fall")
SIZES: Final = ("S", "M", "L", "XL")
CATEGORIES: Final = ("Clothing", "Footwear", "Outerwear", "Accessories")
YES_NO: Final = ("Yes", "No")

# Frecuencia original -> (etiqueta normalizada, días entre compras).
# Fortnightly y Bi-Weekly son sinónimos, igual que Quarterly y Every 3 Months.
FREQUENCIES: Final[dict[str, tuple[str, int]]] = {
    "Weekly": ("weekly", 7),
    "Fortnightly": ("biweekly", 14),
    "Bi-Weekly": ("biweekly", 14),
    "Monthly": ("monthly", 30),
    "Quarterly": ("quarterly", 90),
    "Every 3 Months": ("quarterly", 90),
    "Annually": ("annually", 365),
}

# (límite inferior inclusivo, etiqueta), en orden ascendente.
AGE_BANDS: Final[tuple[tuple[int, str], ...]] = (
    (18, "18-24"),
    (25, "25-34"),
    (35, "35-44"),
    (45, "45-54"),
    (55, "55-64"),
    (65, "65+"),
)
