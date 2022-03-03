from pathlib import Path
import json

leis_table = Path("../tables/leis").absolute()

for p in leis_table.iterdir():
    if p.suffix == ".json":
        with open(p, "r") as f:
            metadata = json.load(f)
        for spectrum_name, spectrum_metadata in metadata["data"].items():
            pickle_name = spectrum_metadata["pickle_name"]
            new_pickle_name = pickle_name.replace(":", "_")
            metadata["data"][spectrum_name]["pickle_name"] = new_pickle_name
        with open(p, "w") as f:
            json.dump(metadata, f, indent=4)
