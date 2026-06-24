# ebird2CBRO

`ebird2CBRO` is a Python package to convert eBird species lists into presence/absence columns in the Brazilian CBRO bird checklist.

## Main idea

The package receives a species list from:

- an eBird checklist;
- an eBird hotspot;
- a spreadsheet exported from eBird.

Then it matches the species with the CBRO checklist and adds a presence column.

## Basic usage

```python
from ebird2cbro import ebird2cbro

df = ebird2cbro(
    cbro_path="CBRO.xlsx",
    source="S123456789",
    source_type="checklist",
    column_name="my_checklist",
    api_key="YOUR_EBIRD_API_KEY"
)