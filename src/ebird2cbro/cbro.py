from importlib.resources import files
import pandas as pd

def get_package_data_path(filename):
    return files("ebird2cbro").joinpath("data", filename)

def load_cbro(cbro_path):
    return pd.read_excel(cbro_path)

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

def detect_ebird_export_columns(species_df):
    metadata_cols = ["Category", "Scientific name", "Species", "Sum"]

    checklist_cols = [
        col for col in species_df.columns
        if col not in metadata_cols
    ]

    return checklist_cols

def standardize_column_name(name):
    return (
        str(name)
        .strip()
        .replace(" ", "_")
        .replace("--", "_")
        .replace(",", "")
        .replace(".", "")
    )

def load_ebird_export_file(species_file):
    if species_file.endswith(".csv"):
        df = pd.read_csv(species_file)
    elif species_file.endswith((".xlsx", ".xls")):
        df = pd.read_excel(species_file)
    else:
        raise ValueError("O arquivo deve ser .csv, .xlsx ou .xls")

    if "Scientific name" not in df.columns:
        raise ValueError("A planilha exportada do eBird precisa ter a coluna 'Scientific name'.")

    checklist_cols = detect_ebird_export_columns(df)

    species_rows = df["Scientific name"].notna()

    output = pd.DataFrame()
    output["scientific_name"] = df.loc[species_rows, "Scientific name"].astype(str).str.strip()

    for col in checklist_cols:
        new_col = standardize_column_name(col)

        output[new_col] = (
            df.loc[species_rows, col]
            .notna()
            .astype(int)
            .values
        )

    return output

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

def add_multiple_presence_columns(
    cbro_df,
    species_df,
    cbro_species_col="Nome do táxon (sem autoria)",
    species_col="scientific_name",
    cbro_rank_col="Categoria",
    species_rank_value="Espécie"
):
    checklist_cols = [
        col for col in species_df.columns
        if col != species_col
    ]

    is_species = cbro_df[cbro_rank_col] == species_rank_value

    for col in checklist_cols:
        present_species = species_df.loc[
            species_df[col] == 1,
            species_col
        ].dropna().astype(str).str.strip().unique()

        cbro_df[col] = None

        cbro_df.loc[is_species, col] = (
            cbro_df.loc[is_species, cbro_species_col]
            .astype(str)
            .str.strip()
            .isin(present_species)
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
        crosswalk = load_default_crosswalk()
    else:
        crosswalk = pd.read_csv(crosswalk_path)

    crosswalk[ebird_col] = crosswalk[ebird_col].astype(str).str.strip()
    crosswalk[cbro_col] = crosswalk[cbro_col].astype(str).str.strip()

    name_map = dict(zip(crosswalk[ebird_col], crosswalk[cbro_col]))

    species_df = species_df.copy()
    species_df[species_col] = species_df[species_col].astype(str).str.strip()
    species_df[species_col] = species_df[species_col].replace(name_map)

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