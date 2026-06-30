from .api import (
    get_species_codes_from_checklist,
    get_species_codes_from_hotspot,
    species_codes_to_dataframe
)

from .cbro import (
    apply_taxonomic_crosswalk,
    load_cbro,
    load_default_cbro,
    load_ebird_export_file,
    add_presence_column,
    add_multiple_presence_columns
)

def ebird2cbro(
    source,
    source_type,
    column_name=None,
    cbro_path=None,
    api_key=None,
    cbro_species_col="Nome do táxon (sem autoria)",
    species_col="scientific_name",
    crosswalk_path=None,
    output_path=None
):
    """
    Add an eBird species list as a presence/absence column in the CBRO checklist.

    Parameters
    ----------
    cbro_path : str
        Path to the CBRO spreadsheet.

    source : str
        eBird checklist ID, hotspot ID (or path to a species file #coming soon).

    source_type : str
        One of: "checklist", "hotspot" (or "file" #coming soon).

    column_name : str
        Name of the presence/absence column to be added.

    api_key : str, optional
        eBird API key. Required for "checklist" and "hotspot".

    cbro_species_col : str, optional
        Name of the column in the CBRO spreadsheet containing species names.

    species_col : str, optional
        Name of the column in the species list containing species names.

    crosswalk_path : str, optional
        Path to the taxonomic crosswalk file.

    output_path : str, optional
        If provided, saves the resulting spreadsheet.

    Returns
    -------
    pandas.DataFrame
        CBRO checklist with the new presence/absence column.
    """

    if cbro_path is None:
        cbro_df = load_default_cbro()
    else:
        cbro_df = load_cbro(cbro_path)

    if source_type == "checklist":
        if api_key is None:
            raise ValueError("api_key é obrigatório para source_type='checklist'.")

        species_codes = get_species_codes_from_checklist(source, api_key)
        species_df = species_codes_to_dataframe(species_codes, api_key)

    elif source_type == "hotspot":
        if api_key is None:
            raise ValueError("api_key é obrigatório para source_type='hotspot'.")

        species_codes = get_species_codes_from_hotspot(source, api_key)
        species_df = species_codes_to_dataframe(species_codes, api_key)

    elif source_type == "file":
        species_df = load_ebird_export_file(source)

    else:
        raise ValueError("source_type deve ser 'checklist', 'hotspot' ou 'file'.")

    species_df = apply_taxonomic_crosswalk(
        species_df,
        crosswalk_path=crosswalk_path,
        species_col=species_col
    )

    if source_type == "file":
        result = add_multiple_presence_columns(
            cbro_df=cbro_df,
            species_df=species_df,
            cbro_species_col=cbro_species_col,
            species_col=species_col
        )
    else:
        if column_name is None:
            raise ValueError("column_name é obrigatório para source_type='checklist' ou 'hotspot'.")

        result = add_presence_column(
            cbro_df=cbro_df,
            species_df=species_df,
            column_name=column_name,
            cbro_species_col=cbro_species_col,
            species_col=species_col
        )

    if output_path is not None:
        result.to_excel(output_path, index=False)

    return result