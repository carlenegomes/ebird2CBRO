import requests
import pandas as pd


EBIRD_TAXONOMY_URL = "https://api.ebird.org/v2/ref/taxonomy/ebird?fmt=json"


def get_ebird_taxonomy(api_key):
    headers = {"X-eBirdApiToken": api_key}
    response = requests.get(EBIRD_TAXONOMY_URL, headers=headers)
    response.raise_for_status()

    taxonomy = response.json()
    return {sp["speciesCode"]: sp for sp in taxonomy}


def get_species_codes_from_checklist(sub_id, api_key):
    url = f"https://api.ebird.org/v2/product/checklist/view/{sub_id}"
    headers = {"X-eBirdApiToken": api_key}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    observations = data.get("obs", [])

    return sorted(set(obs["speciesCode"] for obs in observations))


def get_checklist_counts(sub_id, api_key, x_value=1):
    """
    Return the number of individuals per species in an eBird checklist.

    Returns
    -------
    counts : dict
        {speciesCode: count}
    x_codes : list
        Species codes reported with "X" (present, but no count).
        These receive `x_value` in `counts`.
    """
    url = f"https://api.ebird.org/v2/product/checklist/view/{sub_id}"
    headers = {"X-eBirdApiToken": api_key}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    observations = response.json().get("obs", [])

    counts = {}
    x_codes = []

    for obs in observations:
        code = obs["speciesCode"]
        raw = obs.get("howManyStr")

        try:
            n = int(raw)
        except (TypeError, ValueError):
            # "X" (or missing): present, but the number was not recorded
            n = x_value
            x_codes.append(code)

        counts[code] = counts.get(code, 0) + n

    return counts, sorted(set(x_codes))


def get_species_codes_from_hotspot(hotspot_id, api_key):
    url = f"https://api.ebird.org/v2/product/spplist/{hotspot_id}"
    headers = {"X-eBirdApiToken": api_key}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return sorted(set(response.json()))


def species_codes_to_dataframe(species_codes, api_key, counts=None):
    taxonomy = get_ebird_taxonomy(api_key)

    records = []

    for code in species_codes:
        info = taxonomy.get(code, {})

        record = {
            "common_name": info.get("comName"),
            "scientific_name": info.get("sciName"),
            "ebird_code": code
        }

        if counts is not None:
            record["abundance"] = counts.get(code, 0)

        records.append(record)

    return pd.DataFrame(records)