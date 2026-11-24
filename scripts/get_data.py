"""Download the two public datasets (no login) into data/.

  GSS cumulative file 1972-2024 (NORC), Stata format
  2022 ACS 1-year PUMS, Pennsylvania person file (U.S. Census Bureau)

  python scripts/get_data.py
"""
import pathlib
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILES = {
    "raw_gss": "https://gss.norc.org/content/dam/gss/get-the-data/documents/stata/GSS_stata.zip",
    "raw_acs": "https://www2.census.gov/programs-surveys/acs/data/pums/2022/1-Year/csv_ppa.zip",
}

for sub, url in FILES.items():
    d = ROOT / "data" / sub
    d.mkdir(parents=True, exist_ok=True)
    z = d / url.rsplit("/", 1)[1]
    if not z.exists():
        print("downloading", url)
        urllib.request.urlretrieve(url, z)
    with zipfile.ZipFile(z) as f:
        f.extractall(d)
    print("extracted", z)
