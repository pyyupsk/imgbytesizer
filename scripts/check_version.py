import requests
import tomli

# Read local version from pyproject.toml
with open("pyproject.toml", "rb") as f:
  pyproject = tomli.load(f)
  local_version = pyproject["project"]["version"]

# Fetch current version on PyPI
response = requests.get("https://pypi.org/pypi/imgbytesizer/json")
if response.status_code == 200:
  published_version = response.json()["info"]["version"]
else:
  raise RuntimeError("Failed to fetch version from PyPI")

# Compare versions
if local_version == published_version:
  raise SystemExit(f"❌ Version {local_version} is already published on PyPI!")
else:
  print(f"✅ Version {local_version} is not yet published on PyPI (latest is {published_version})")
