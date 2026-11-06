from .api import (
    get_checklist_counts,
    get_species_codes_from_checklist,
    get_species_codes_from_hotspot,
    species_codes_to_dataframe
)

from .cbro import (
    apply_taxonomic_crosswalk,
    load_cbro,
    load_default_cbro,
    load_ebird_export_file,
    check_value_type,
    add_presence_column,
    add_multiple_presence_columns,
    find_unmatched_species
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
    output_path=None,
    show_unmatched=True,
    value_type="presence",
    x_value=1
):
    """
    Add an eBird species list as a presence/absence column in the CBRO checklist.

    Parameters
    ----------
    source : str
        eBird checklist ID, hotspot ID (or path to a species file #coming soon).

    source_type : str
        One of: "checklist", "hotspot" (or "file" #coming soon).

    column_name : str
        Name of the presence/absence column to be added.

    cbro_path : str
        Path to the CBRO spreadsheet.

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

    show_unmatched : bool, optional
        If True, prints species that could not be matched to the CBRO list.

    value_type : str, optional
        "presence" (default): columns with 1 (recorded) / 0 (not recorded).
        "abundance": columns with the number of individuals (0 = not
        recorded). Works with "checklist" and "file"; not available for
        "hotspot", because the eBird API only returns the species list
        of a hotspot, without counts.

    x_value : int, optional
        Only for value_type="abundance". Value used when a species was
        recorded as "X" (present, but not counted). Default is 1.

    Returns
    -------
    pandas.DataFrame
        CBRO checklist with the new presence/absence column.
    """

    check_value_type(value_type)

    if cbro_path is None:
        cbro_df = load_default_cbro()
    else:
        cbro_df = load_cbro(cbro_path)

    if source_type == "checklist":
        if api_key is None:
            raise ValueError("api_key é obrigatório para source_type='checklist'.")

        if value_type == "abundance":
            counts, x_codes = get_checklist_counts(source, api_key, x_value)
            species_df = species_codes_to_dataframe(
                list(counts), api_key, counts=counts
            )

            if x_codes:
                print(
                    f"{len(x_codes)} espécie(s) foram registradas com 'X' "
                    f"(sem contagem) e receberam o valor {x_value}."
                )
        else:
            species_codes = get_species_codes_from_checklist(source, api_key)
            species_df = species_codes_to_dataframe(species_codes, api_key)

    elif source_type == "hotspot":
        if api_key is None:
            raise ValueError("api_key é obrigatório para source_type='hotspot'.")

        if value_type == "abundance":
            raise ValueError(
                "value_type='abundance' não está disponível para hotspots: "
                "a API do eBird retorna só a lista de espécies, sem contagens. "
                "Use 'presence', ou exporte os dados e use source_type='file'."
            )

        species_codes = get_species_codes_from_hotspot(source, api_key)
        species_df = species_codes_to_dataframe(species_codes, api_key)

    elif source_type == "file":
        species_df = load_ebird_export_file(source, value_type, x_value)

    else:
        raise ValueError("source_type deve ser 'checklist', 'hotspot' ou 'file'.")

    species_df = apply_taxonomic_crosswalk(
        species_df,
        crosswalk_path=crosswalk_path,
        species_col=species_col
    )

    unmatched = find_unmatched_species(
        cbro_df=cbro_df,
        species_df=species_df,
        cbro_species_col=cbro_species_col,
        species_col=species_col
    )

    if show_unmatched:
        if len(unmatched) == 0:
            print("Todas as espécies foram associadas com sucesso à lista CBRO :D")
        else:
            if len(unmatched) == 1:
                print("1 espécie não pôde ser associada à lista CBRO...")
            else:
                print(f"{len(unmatched)} espécies não puderam ser associadas à lista CBRO...")
            for sp in unmatched:
                print(f" - {sp}")

    if source_type == "file":
        result = add_multiple_presence_columns(
            cbro_df=cbro_df,
            species_df=species_df,
            cbro_species_col=cbro_species_col,
            species_col=species_col,
            value_type=value_type
        )
    else:
        if column_name is None:
            raise ValueError("column_name é obrigatório para source_type='checklist' ou 'hotspot'.")

        result = add_presence_column(
            cbro_df=cbro_df,
            species_df=species_df,
            column_name=column_name,
            cbro_species_col=cbro_species_col,
            species_col=species_col,
            value_col="abundance" if value_type == "abundance" else None
        )

    if output_path is not None:
        result.to_excel(output_path, index=False)

    return result