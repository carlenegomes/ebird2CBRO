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

def match_species(
    species_df,
    species_col="scientific_name",
    cbro_path=None,
    crosswalk_path=None,
    crosswalk_source_col="ebird_name",
    crosswalk_cbro_col="cbro_name",
    cbro_species_col="Nome do táxon (sem autoria)",
    cbro_rank_col="Categoria",
    species_rank_value="Espécie"
):
    """
    Associa nomes científicos de uma tabela à taxonomia da CBRO.

    A função:
    1. preserva todas as colunas originais;
    2. tenta correspondência direta com a CBRO;
    3. quando necessário, aplica o crosswalk taxonômico;
    4. adiciona o nome aceito pela CBRO;
    5. informa o tipo de associação realizada.

    Parameters
    ----------
    species_df : pandas.DataFrame
        DataFrame contendo os nomes científicos.

    species_col : str, default "scientific_name"
        Coluna do DataFrame que contém os nomes científicos.

    cbro_path : str ou Path, optional
        Caminho para uma lista CBRO alternativa.
        Quando None, usa a lista incluída no pacote.

    crosswalk_path : str ou Path, optional
        Caminho para um crosswalk alternativo.
        Quando None, usa o crosswalk incluído no pacote.

    crosswalk_source_col : str, default "ebird_name"
        Coluna do crosswalk com o nome usado na fonte original.

    crosswalk_cbro_col : str, default "cbro_name"
        Coluna do crosswalk com o nome aceito pela CBRO.

    cbro_species_col : str
        Coluna da lista CBRO com o nome científico sem autoria.

    cbro_rank_col : str
        Coluna da CBRO com a categoria taxonômica.

    species_rank_value : str
        Valor usado pela CBRO para identificar espécies.

    Returns
    -------
    pandas.DataFrame
        DataFrame original com as colunas adicionais:

        - scientific_name_original
        - scientific_name_cbro
        - match_status
        - matched
    """

    if not isinstance(species_df, pd.DataFrame):
        raise TypeError(
            "species_df precisa ser um pandas.DataFrame."
        )

    if species_col not in species_df.columns:
        raise ValueError(
            f"A coluna '{species_col}' não existe no DataFrame. "
            f"Colunas disponíveis: {species_df.columns.tolist()}"
        )

    # Carrega a lista da CBRO
    if cbro_path is None:
        cbro_df = load_default_cbro()
    else:
        cbro_df = load_cbro(cbro_path)

    # Mantém apenas registros no nível de espécie
    cbro_species = cbro_df.loc[
        cbro_df[cbro_rank_col] == species_rank_value
    ].copy()

    cbro_species[cbro_species_col] = (
        cbro_species[cbro_species_col]
        .astype(str)
        .str.strip()
    )

    accepted_names = set(
        cbro_species[cbro_species_col]
        .dropna()
        .unique()
    )

    result = species_df.copy()

    # Preserva o nome original
    result["scientific_name_original"] = (
        result[species_col]
        .astype("string")
        .str.strip()
    )

    result["scientific_name_cbro"] = result[
        "scientific_name_original"
    ]

    # Correspondência direta
    exact_match = result[
        "scientific_name_original"
    ].isin(accepted_names)

    result["match_status"] = "unmatched"

    result.loc[
        exact_match,
        "match_status"
    ] = "exact_cbro"

    # Carrega o crosswalk
    if crosswalk_path is None:
        crosswalk = load_default_crosswalk()
    else:
        crosswalk = pd.read_csv(crosswalk_path)

    required_crosswalk_columns = {
        crosswalk_source_col,
        crosswalk_cbro_col
    }

    missing_crosswalk_columns = (
        required_crosswalk_columns - set(crosswalk.columns)
    )

    if missing_crosswalk_columns:
        raise ValueError(
            "Colunas ausentes no crosswalk: "
            f"{sorted(missing_crosswalk_columns)}. "
            f"Colunas disponíveis: {crosswalk.columns.tolist()}"
        )

    crosswalk = crosswalk.copy()

    crosswalk[crosswalk_source_col] = (
        crosswalk[crosswalk_source_col]
        .astype(str)
        .str.strip()
    )

    crosswalk[crosswalk_cbro_col] = (
        crosswalk[crosswalk_cbro_col]
        .astype(str)
        .str.strip()
    )

    name_map = dict(
        zip(
            crosswalk[crosswalk_source_col],
            crosswalk[crosswalk_cbro_col]
        )
    )

    # Aplica crosswalk apenas aos nomes sem match direto
    unmatched_mask = ~exact_match

    mapped_names = (
        result.loc[
            unmatched_mask,
            "scientific_name_original"
        ]
        .map(name_map)
    )

    valid_crosswalk_match = (
        mapped_names.notna()
        & mapped_names.isin(accepted_names)
    )

    valid_indices = mapped_names.index[
        valid_crosswalk_match
    ]

    result.loc[
        valid_indices,
        "scientific_name_cbro"
    ] = mapped_names.loc[valid_indices]

    result.loc[
        valid_indices,
        "match_status"
    ] = "crosswalk"

    # Entradas vazias
    missing_input = (
        result["scientific_name_original"].isna()
        | result["scientific_name_original"].eq("")
    )

    result.loc[
        missing_input,
        "scientific_name_cbro"
    ] = pd.NA

    result.loc[
        missing_input,
        "match_status"
    ] = "missing_input"

    result["matched"] = result[
        "match_status"
    ].isin(["exact_cbro", "crosswalk"])

    return result

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