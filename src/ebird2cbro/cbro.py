import pandas as pd

def load_cbro(cbro_path):
    return pd.read_excel(cbro_path)


def load_species_file(species_file):
    if species_file.endswith(".csv"):
        return pd.read_csv(species_file)

    if species_file.endswith((".xlsx", ".xls")):
        return pd.read_excel(species_file)

    raise ValueError("O arquivo deve ser .csv, .xlsx ou .xls")

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