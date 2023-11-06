""""
YAXArray of dimensions (:timesteps, :scenarios, : species, :locations). For each coral
species and location there are 100 cyclone category projections for 100 timesteps. Cyclone
categories goes from 1 to 6, where 1 is no cyclone and 2 to 6 correspond to BOM's categories
1 to 5.
"""
function cyclone_scenarios(rrap_gdf::DataFrame, rme_dpkg_path::String)::YAXArray
    # Filter rrap_gdf reef locations by rme_gdf reefs
    rme_gdf::DataFrame = _rme_gdf(rme_dpkg_path)
    match_ids = _match_gdf_ids(rme_gdf, rrap_gdf)
    reef_filters::YAXArray = _reef_filters(rme_gdf, rrap_gdf, match_ids)

    SPECIES = [
        "abhorescent_acropora",
        "tabular_acropora",
        "corymbose_acropora",
        "corymbose_non_acropora",
        "small_massives",
        "large_massives",
    ]

    input_folder = joinpath(rme_dpkg_path, "data_files", "cyc_csv")
    scen_files = readdir(input_folder)

    # This is only to determine number of timesteps and locations
    tmp_file = CSV.read(
        joinpath(input_folder, scen_files[1]),
        DataFrame;
        stringtype=String,
        header=false,
        comment="#"
    )

    locations = rrap_gdf.reef_siteid

    n_timesteps = length(tmp_file[1, 2:end])
    n_locations = length(locations)
    n_species = length(SPECIES)
    n_scenarios = length(scen_files)

    axlist = (
        Dim{:timesteps}(1:n_timesteps),
        Dim{:locations}(locations),
        Dim{:species}(SPECIES),
        Dim{:scenarios}(1:n_scenarios),
    )

    scenarios = YAXArray(axlist, zeros(n_timesteps, n_locations, n_species, n_scenarios))

    # Each file is a scenario
    for (idx_s, file) in enumerate(scen_files)
        filepath = joinpath(input_folder, file)
        tmp_scen = CSV.read(
            filepath, DataFrame; stringtype=String, header=false, comment="#"
        )
        scen = DataFrame(Matrix(tmp_scen[:, 2:end])', tmp_scen[:, 1])

        for label in reef_filters.labels
            # Add 1 so category 0 coresponds to idx 1, etc
            cyc_categories = scen[:, label] .+ 1
            reef_filter = dropdims(reef_filters[reef_filters.labels.==label, :]; dims=1)
            @views scenarios[:, reef_filter, :, At(idx_s)] .= cyc_categories
        end
    end

    return scenarios
end

function _rme_gdf(rme_dpkg_path::String)::DataFrame
    return GDF.read(joinpath(rme_dpkg_path, "data_files", "region", "reefmod_gbr.gpkg"))
end

"""
Vector of ids from the large_df for reefs that intersect any of the reefs from the small_df
"""
function _match_gdf_ids(large_gdf::DataFrame, small_gdf::DataFrame)
    return unique(
        vcat(
            [findall(GDF.intersects.(large_gdf.geom, [geom])) for geom in small_gdf.geom]...
        ),
    )
end

"""
Returns a YAXArray with dimensions (:labels, :filters) where :labels are LABEL_IDs for rme
reefs and :filters are booleans each rrap location that are true when that rrap location
belongs to the correspondent rme reef
"""
function _reef_filters(rme_gdf::DataFrame, rrap_gdf::DataFrame, match_ids::Vector)::YAXArray
    rme_names = lowercase.(rme_gdf[match_ids, :].GBR_NAME)
    rrap_names = lowercase.(rrap_gdf.Reef)

    # Filter sites for each reef
    rrap_ids = rrap_gdf.reef_siteid
    sites_by_reef = [
        rrap_ids .∈ [rrap_gdf[occursin.(rrap_names, rme_name), "reef_siteid"]] for
        rme_name in rme_names
    ]

    rme_label_ids = rme_gdf[match_ids, :].LABEL_ID
    axlist = (Dim{:labels}(rme_label_ids), Dim{:filters}(1:length(rrap_names)))
    return YAXArray(axlist, hcat(sites_by_reef...)')
end
