# data/codes_m18.py
"""Liste exhaustive des 94 codes ROME du domaine M18 (Informatique).
Source : référentiel ROME v4.6, France Travail."""

CODES_M18 = [
    "M1801", "M1802", "M1803", "M1804", "M1805", "M1806", "M1807",
    "M1808", "M1809", "M1810", "M1811", "M1812", "M1813", "M1814",
    "M1815", "M1816", "M1817", "M1818", "M1819", "M1820", "M1821",
    "M1822", "M1823", "M1824", "M1825", "M1826", "M1827", "M1828",
    "M1829", "M1830", "M1831", "M1832", "M1833", "M1834", "M1835",
    "M1836", "M1837", "M1838", "M1839", "M1840", "M1841", "M1842",
    "M1843", "M1844", "M1845", "M1846", "M1847", "M1848", "M1849",
    "M1850", "M1851", "M1852", "M1853", "M1854", "M1855", "M1856",
    "M1857", "M1858", "M1859", "M1860", "M1861", "M1862", "M1863",
    "M1864", "M1865", "M1866", "M1867", "M1868", "M1869", "M1870",
    "M1871", "M1872", "M1873", "M1874", "M1875", "M1876", "M1877",
    "M1878", "M1879", "M1880", "M1881", "M1882", "M1883", "M1884",
    "M1885", "M1886", "M1887", "M1888", "M1889", "M1890", "M1891",
    "M1892", "M1893", "M1894"
]

# Codes hors scope (météorologie) — à exclure du scrape et de l'éval
CODES_METEO_HORS_SCOPE = ["M1807", "M1808", "M1809", "M1888", "M1890", "M1891", "M1893"]

# Codes utiles pour le projet (informatique stricto sensu)
CODES_INFO_M18 = [c for c in CODES_M18 if c not in CODES_METEO_HORS_SCOPE]
# → 87 codes
