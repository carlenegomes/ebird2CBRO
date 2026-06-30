from importlib.resources import files
import pandas as pd

def get_package_data_path(filename):
    return files("ebird2cbro").joinpath("data", filename)

def load_default_cbro():
    path = get_package_data_path("cbro.xlsx")
    return pd.read_excel(path)

def load_default_crosswalk():
    path = get_package_data_path("taxonomic_crosswalk.csv")
    return pd.read_csv(path)

def standardize_species_file(species_df):
    """
    Standardize species files to use a 'scientific_name' column.

    Supports:
    - eBird exported spreadsheets with 'Scientific name'
    - files already containing 'scientific_name'
    """

    species_df = species_df.copy()

    if "scientific_name" in species_df.columns:
        species_df = species_df[["scientific_name"]]

    elif "Scientific name" in species_df.columns:
        species_df = species_df.rename(columns={"Scientific name": "scientific_name"})

        if "Sum" in species_df.columns:
            species_df = species_df[species_df["Sum"].notna()]

        species_df = species_df[["scientific_name"]]

    else:
        raise ValueError(
            "Não encontrei uma coluna de nome científico. "
            "Use uma coluna chamada 'scientific_name' ou 'Scientific name'."
        )

    species_df = species_df.dropna(subset=["scientific_name"])
    species_df["scientific_name"] = species_df["scientific_name"].astype(str).str.strip()
    species_df = species_df.drop_duplicates()

    return species_df


def load_species_file(species_file):
    if species_file.endswith(".csv"):
        species_df = pd.read_csv(species_file)

    elif species_file.endswith((".xlsx", ".xls")):
        species_df = pd.read_excel(species_file)

    else:
        raise ValueError("O arquivo deve ser .csv, .xlsx ou .xls")

    return standardize_species_file(species_df)

def add_presence_column(
    cbro_df,
    species_df,
    column_name,
    cbro_species_col="Nome do táxon (sem autoria)",
    species_col="scientific_name",
    cbro_rank_col="Categoria",
    species_rank_value="Espécie"
):
    species = species_df[species_col].dropna().astype(str).str.strip().unique()

    is_species = cbro_df[cbro_rank_col] == species_rank_value

    cbro_df[column_name] = None

    cbro_df.loc[is_species, column_name] = (
        cbro_df.loc[is_species, cbro_species_col]
        .astype(str)
        .str.strip()
        .isin(species)
        .astype(int)
    )

    return cbro_df

def apply_taxonomic_crosswalk(
    species_df,
    crosswalk_path=None,
    species_col="scientific_name",
    ebird_col="ebird_name",
    cbro_col="cbro_name"
):
    if crosswalk_path is None:
        return species_df

    crosswalk = pd.read_csv(crosswalk_path)

    name_map = dict(zip(crosswalk[ebird_col], crosswalk[cbro_col]))

    species_df = species_df.copy()
    species_df[species_col] = (
        species_df[species_col]
        .replace(name_map)
    )

    return species_df

def find_unmatched_species(
    cbro_df,
    species_df,
    cbro_species_col="Nome do táxon (sem autoria)",
    species_col="scientific_name"
):
    cbro_species = set(
        cbro_df[cbro_species_col]
        .dropna()
        .astype(str)
        .str.strip()
    )

    input_species = set(
        species_df[species_col]
        .dropna()
        .astype(str)
        .str.strip()
    )

    unmatched = sorted(input_species - cbro_species)

    return unmatched