from .api import (
    get_species_codes_from_checklist,
    get_species_codes_from_hotspot,
    species_codes_to_dataframe
)

from .cbro import (
    load_cbro,
    load_species_file,
    add_presence_column
)


def ebird2cbro(
    cbro_path,
    source,
    source_type,
    column_name,
    api_key=None,
    output_path=None,
    cbro_species_col="Nome do táxon (sem autoria)",
    species_col="scientific_name"
):
    """
    Add an eBird species list as a presence/absence column in the CBRO checklist.

    Parameters
    ----------
    cbro_path : str
        Path to the CBRO spreadsheet.

    source : str
        eBird checklist ID, hotspot ID, or path to a species file.

    source_type : str
        One of: "checklist", "hotspot", or "file".

    column_name : str
        Name of the presence/absence column to be added.

    api_key : str, optional
        eBird API key. Required for "checklist" and "hotspot".

    output_path : str, optional
        If provided, saves the resulting spreadsheet.

    Returns
    -------
    pandas.DataFrame
        CBRO checklist with the new presence/absence column.
    """

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
        species_df = load_species_file(source)

    else:
        raise ValueError("source_type deve ser 'checklist', 'hotspot' ou 'file'.")

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