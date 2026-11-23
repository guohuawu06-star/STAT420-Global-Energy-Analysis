from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
PROCESSED = ROOT / "data/processed"
META = ROOT / "data/metadata"
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
VERSION = "2026-09-10"
RELEASE = "owid-energy-" + VERSION
PINNED = f"https://catalog.ourworldindata.org/garden/energy/{VERSION}/owid_energy/"
SOURCE_URL = PINNED + "owid_energy.csv"
SOURCE_SHA256 = "238177564d56b21fd40caaf9572ad8f8382421899462c68952294fcce4f2eea9"
START_YEAR = 2000
PLACES = {"World": None, "China": "CHN", "India": "IND", "Germany": "DEU", "United States": "USA"}
CATEGORIES = {
    "total_energy_twh": "Total", "coal_energy_share_pct": "Coal", "oil_energy_share_pct": "Oil",
    "gas_energy_share_pct": "Natural gas", "renewables_energy_share_pct": "Renewables",
    "fossil_fuels_energy_share_pct": "Fossil fuels", "nuclear_energy_share_pct": "Nuclear",
}
TOTAL = "total_energy_twh"
RENEWABLE = "renewables_energy_share_pct"
