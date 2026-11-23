import hashlib
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from src.config import META, RAW, SOURCE_SHA256, SOURCE_URL, VERSION


def download():
    RAW.mkdir(parents=True, exist_ok=True)
    META.mkdir(parents=True, exist_ok=True)
    path = RAW / "owid_energy.csv"
    manifest = META / "provenance.json"
    if path.exists():
        data = path.read_bytes()
        acquired = None
        if manifest.exists():
            previous = json.loads(manifest.read_text(encoding="utf-8")).get(path.name, {})
            if previous.get("sha256") == SOURCE_SHA256 and previous.get("url") == SOURCE_URL:
                acquired = previous.get("acquired_utc")
    else:
        request = Request(SOURCE_URL, headers={"User-Agent": "STAT420 academic replication"})
        with urlopen(request, timeout=90) as response:
            data = response.read()
        acquired = datetime.now(timezone.utc).isoformat()
    digest = hashlib.sha256(data).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError(f"{path}: SHA-256 differs from the pinned OWID release.")
    if not path.exists():
        with path.open("xb") as output:
            output.write(data)
    records = {path.name: dict(url=SOURCE_URL, format="CSV", version=VERSION, bytes=len(data),
                               sha256=digest, acquired_utc=acquired,
                               verified_utc=datetime.now(timezone.utc).isoformat())}
    manifest.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return records


if __name__ == "__main__":
    download()
