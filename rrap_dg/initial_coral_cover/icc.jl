"""
This script takes initial coral covers at a lower spatial resolution and extrapolates these
for a smaller spatial domain (i.e., downscaling).

Note: Source data is expected to be relative to absolute area. This is transformed to
      be relative to \$k\$ area (i.e., maximum carrying capacity) for use in ADRIA.

      A lot of manual transformations are currently necessary to adjust RME data
      (e.g., typos in reef location IDs, conversion of areal units, etc)

TODO: Update to use rrap-dg data packages and not rely on RME datasets directly.
"""

using
    CSV,
    DataFrames,
    NetCDF,
    TOML,
    YAXArrays

using
    Distributions,
    Statistics

import ArchGDAL as AG
import GeoDataFrames as GDF
import GeoDataFrames.GeoInterface as GI
import YAXArrays.DD: At

"""
    _colony_mean_area(colony_diam_means::Array{T})::Array{T} where {T<:Real}

Generate mean colony areas for given colony diameter(s).

# Arguments
- `colony_diam_means` : mean colony diameter (in meters)
"""
function _colony_mean_area(colony_diam_means::Array{T})::Array{T} where {T<:Float64}
    return pi .* ((colony_diam_means ./ 2.0) .^ 2)
end

"""
    _convert_abs_to_k(coral_cover::Union{NamedDimsArray,Matrix{Float64}}, spatial::DataFrame)::Union{NamedDimsArray,Matrix{Float64}}

Convert coral cover data from being relative to absolute location area to relative to
\$k\$ area.
"""
function _convert_abs_to_k(
    coral_cover::Union{YAXArray,Matrix{Float64}}, spatial::DataFrame
)::Union{YAXArray,Matrix{Float64}}
    # Initial coral cover is provided as values relative to location area.
    # Convert coral covers to be relative to k area, ignoring locations with 0 carrying
    # capacity (k area = 0.0).
    absolute_k_area = (spatial.k .* spatial.area)'  # max possible coral area in m^2
    valid_locs::BitVector = absolute_k_area' .> 0.0
    coral_cover[:, valid_locs] .= (
        (coral_cover[:, valid_locs] .* spatial.area[valid_locs]') ./
        absolute_k_area[valid_locs]'
    )

    # Ensure initial coral cover values are <= maximum carrying capacity
    @assert all(sum(coral_cover; dims=1) .<= 1.0) "Max: $(maximum(sum(coral_cover; dims=1)))"

    return coral_cover
end

"""
    _get_id_dir(dpkg_path::String)::String

Return directory holding reef id lists.
"""
function _get_id_dir(dpkg_path::String)::String
    if isdir(joinpath(dpkg_path, "spatial"))
        # Old rrap-dg data package
        return joinpath(dpkg_path, "spatial")
    end

    if isdir(joinpath(dpkg_path, "data_files"))
        # ReefMod or RME dataset
        return joinpath(dpkg_path, "data_files", "id")
    end

    error("Unknown directory structure.")
end

"""
    _get_gbr_gpkg(dpkg_path::String)::String

Return path to GBR-wide geospatial data.
"""
function _get_gbr_gpkg(dpkg_path::String)::String
    if isdir(joinpath(dpkg_path, "spatial"))
        # Old rrap-dg data package
        return joinpath(dpkg_path, "spatial", "reefmod_gbr.gpkg")
    end

    if isdir(joinpath(dpkg_path, "data_files"))
        # ReefMod or RME dataset
        return joinpath(dpkg_path, "data_files", "region", "reefmod_gbr.gpkg")
    end

    error("Unknown directory structure.")
end

"""
    _get_icc_dir(dpkg_path::String)::String

Return directory holding initial coral cover data.
"""
function _get_icc_dir(dpkg_path::String)::String
    if isdir(joinpath(dpkg_path, "coral_cover"))
        # Old rrap-dg data package
        return joinpath(dpkg_path, "coral_cover")
    end

    if isdir(joinpath(dpkg_path, "data_files", "initial_csv"))

        return joinpath(dpkg_path, "data_files", "initial_csv")
    end

    if isdir(joinpath(dpkg_path, "data_files"))
        # ReefMod or RME dataset
        return joinpath(dpkg_path, "data_files", "initial")
    end

    error("Unknown directory structure.")
end

"""
    _get_icc_cover_files(icc_dir::String)::Vector{String}

Find all the initial coral cover files and return them as full paths.
"""
function _get_icc_cover_files(icc_dir::String)::Vector{String}
    cover_pattern = r"coral_sp[1-6]_\d{4}\.csv"
    files = filter(f -> occursin(cover_pattern, f), readdir(icc_dir))
    if length(files) == 0
        error("Unable to find initial cover files. Unkown directory structure.")
    end
    files = joinpath.(Ref(icc_dir), files)

    return files
end


"""
    load_gbr_gpkg(rrapdg_dpkg_path::String)::DataFrame

Load GBR geopackage associated with RME (v1.0.x) with precomputed/packaged area and
\$k\$ values.

# Arguments
- `rrapdg_dpkg_path` : Path to rrap-dg data package

# Returns
YAXArray[locs, species]
"""
function load_gbr_gpkg(rrapdg_dpkg_path::String)::DataFrame
    id_list = CSV.read(
        joinpath(_get_id_dir(rrapdg_dpkg_path), "id_list_2023_03_30.csv"),
        DataFrame;
        header=false,
        comment="#",
    )

    # Re-order spatial data to match RME dataset
    # MANUAL CORRECTION
    gbr_data = GDF.read(_get_gbr_gpkg(rrapdg_dpkg_path))

    try
        gbr_data[gbr_data.LABEL_ID.=="20198", :LABEL_ID] .= "20-198"
    catch
        gbr_data[gbr_data.RME_GBRMPA_ID.=="20198", :RME_GBRMPA_ID] .= "20-198"
        gbr_data[!, :LABEL_ID] = gbr_data.RME_GBRMPA_ID
    end

    id_order = [first(findall(x .== gbr_data.LABEL_ID)) for x in string.(id_list[:, 1])]
    gbr_data = gbr_data[id_order, :]

    # Check that the two lists of location ids are identical
    @assert isempty(findall(gbr_data.LABEL_ID .!= id_list[:, 1]))

    # Convert area in km² to m²
    gbr_data[:, :area] .= id_list[:, 2] .* 1e6

    # Calculate `k` area (1.0 - "ungrazable" area)
    gbr_data[:, :k] .= 1.0 .- id_list[:, 3]

    return gbr_data
end

"""
    load_rme_cover(rrapdg_dpkg_path::String, gbr_gpkg::DataFrame)::YAXArray

Load mean of initial covers from ReefMod Engine datasets (v1.0.18).

# Arguments
- `rrapdg_dpkg_path` : Path to ReefMod data
- `gbr_gpkg` : ReefMod GBR-scale geopackage

# Returns
YAXArray[locs, species]
"""
function load_rme_cover(rrapdg_dpkg_path::String, gbr_gpkg::DataFrame)::YAXArray
    icc_path = _get_icc_dir(rrapdg_dpkg_path)

    # Identify coral cover files with known prefix pattern
    valid_files = filter(isfile, readdir(icc_path; join=true))
    icc_files = filter(x -> occursin("coral_", basename(x)), valid_files)
    if isempty(icc_files)
        ArgumentError("No coral cover data files found in: $(icc_path)")
    end
    n_species = length(icc_files)
    @assert n_species == 6 "Number of coral files do not match expected number of species (6)"

    # Shape is locations, scenarios, species
    # 20 is the known number of scenarios.
    loc_ids = try
        gbr_gpkg.LABEL_ID
    catch
        gbr_gpkg.RME_LABEL_ID
    end
    icc_data = zeros(length(loc_ids), 20, n_species)
    # Each icc file contains 20 initial coral cover scenarios, as percentage, per location
    for (i, fn) in enumerate(icc_files)
        icc_data[:, :, i] = Matrix(
            CSV.read(fn, DataFrame; drop=[1], header=false, comment="#")
        )
    end

    # Take the mean over repeats, as suggested by YM (pers comm. 2023-02-27 12:40pm AEDT).
    # Convert from percent to relative values.
    icc_mat = Matrix(((dropdims(mean(icc_data; dims=2); dims=2)) ./ 100.0)')

    # Convert values relative to absolute area to values relative to k area
    icc = _convert_abs_to_k(icc_mat, gbr_gpkg)

    return YAXArray(
        (
            Dim{:species}(1:n_species),
            Dim{:locs}(loc_ids)
        ),
        icc
    )
end

"""
    downscale_icc(init_cc::NamedDimsArray, large_ds::DataFrame, small_ds::DataFrame)::Matrix{Float64}

Downscale initial coral cover data from a larger spatial area to a smaller spatial area by
proportioning indicated coral cover for a reef to individual locations within the reef.

Matches locations for a reef by their spatial intersect with a smaller spatial location.

# Arguments
- `init_cc` : Initial coral cover data (relative to each Reef's k area) to downscale
- `large_ds` : data for larger geospatial area
- `small_ds` : data for smaller geospatial area

# Returns
Cover [species ⋅ location] relative to k area.
"""
function downscale_icc(
    init_cc::YAXArray,
    large_ds::DataFrame,
    small_ds::DataFrame
)::YAXArray
    # Find locations in larger spatial dataset that intersect with smaller dataset
    # matching by Reef UNIQUE ID
    match_ids = in.(large_ds.UNIQUE_ID, Ref(small_ds.UNIQUE_ID))

    # Create named ids for functional groups
    taxa_names = [
        "arborescent Acropora",
        "tabular Acropora",
        "corymbose Acropora",
        "corymbose non-Acropora",
        "Small massives",
        "Large massives"
    ]

    # Create storage matrix
    n_species = size(init_cc, :species)
    n_locs = length(small_ds.reef_siteid)
    target_locs_init_cover = YAXArray(
        (
            Dim{:species}(taxa_names),
            Dim{:locations}(small_ds.reef_siteid)
        ),
        zeros(n_species, n_locs)
    )

    # Conver small ds k areas from percentage to fraction
    small_rel_k_areas = (small_ds.k ./ 100)

    # Conver small ds k areas from relative (to total area) to absolute
    small_abs_k_area = (small_rel_k_areas .* small_ds.area)'

    has_capacity = vec(small_abs_k_area .> 0.0)

    # Large ds clusters labels
    reef_labels_large = large_ds[match_ids, :LABEL_ID]
    reef_id_large = replace.(reef_labels_large, "-" => "")

    reef_names_small = unique(small_ds.Reef .|> lowercase)
    for reef_name_small in reef_names_small
        reef_id_small = split(reef_name_small, "_")[end]
        matching_reef = reef_id_large .== reef_id_small
        label = reef_labels_large[matching_reef]

        # Cluster cover relative to Reef area for each species
        reef_rel_cover = dropdims(sum(init_cc[locs=At(label)], dims=2), dims=2)

        # Match up locations based on order indicated by geospatial dataset
        is_cluster = ((small_ds.Reef .|> lowercase) .== reef_name_small)
        relevant_locs = is_cluster .& has_capacity
        n_locs = sum(relevant_locs)

        # Get cover relative to cluster's absolute k area
        target_locs_init_cover[:, relevant_locs] .= repeat(reef_rel_cover.data, 1, n_locs)
    end

    # Sum of species/size class cover should be <= maximum carrying capacity
    @assert all(sum(target_locs_init_cover, dims=1) .<= small_abs_k_area)

    return target_locs_init_cover
end

"""
    downscale_icc(rrapdg_dpkg_path::String, target_gpkg::String, output_path::String)::Nothing

Downscale initial coral covers from ReefMod Engine for a given spatial area and export to
provided output path.

# Arguments
- `rrapdg_dpkg_path` : Path to rrap-dg data package
- `target_gpkg` : Path to geopackage file defining area of interest
- `output_path` : Path to export to resulting netCDF to
"""
function downscale_icc(
    rrapdg_dpkg_path::String,
    target_gpkg_path::String,
    output_path::String
)::Nothing
    gbr_gpkg = load_gbr_gpkg(rrapdg_dpkg_path)
    rme_icc = load_rme_cover(rrapdg_dpkg_path, gbr_gpkg)
    target_gpkg = GDF.read(target_gpkg_path)

    icc = downscale_icc(rme_icc, gbr_gpkg, target_gpkg)

    try
        savecube(icc, output_path, driver=:netcdf)
    catch err
        if err isa ArgumentError
            @info "File appears to already exist or cannot be written to."
        end
    end

    return nothing
end

"""
    _sort_icc_files(filenames::Vector{String})

Sort the initial coral cover files to give ["coral_sp1_2023.csv", "coral_sp2_2023.csv", ...]
"""
function _sort_icc_files(filenames::Vector{String})
    # Guarantee that the order of files is ["sp1", "sp2", "sp3", ...]
    sorted_filenames = sort(
        filenames, by = x -> parse(Int, match(r"sp(\d+)", x).captures[1])
    )
    @assert occursin("sp1", sorted_filenames[1]) &&
            occursin("sp2", sorted_filenames[2]) &&
            occursin("sp3", sorted_filenames[3]) &&
            occursin("sp4", sorted_filenames[4]) &&
            occursin("sp5", sorted_filenames[5]) &&
            occursin("sp6", sorted_filenames[6])

    return sorted_filenames
end

function format_rme_icc(rme_path::String, canonical_path::String, output_path::String)::Nothing
    # Read initial coral cover csvs
    icc_dir::String = _get_icc_dir(rme_path)
    icc_files::Vector{String} = _get_icc_cover_files(icc_dir)
    icc_files = _sort_icc_files(icc_files)
    icc_csvs = [
        CSV.read(icc_fn, DataFrame; comment="#", header=false)
        for icc_fn in icc_files
    ]

    canonical_gpkg = GDF.read(canonical_path)

    # Initial coral cover of shape [locations ⋅ repeats ⋅ functional group]
    init_cover::Array{Float64} = zeros(
        Float64, size(icc_csvs[1], 1), size(icc_csvs[1], 2) - 1, length(icc_csvs)
    )

    ordering_dict = Dict(id=>i for (i, id) in enumerate(canonical_gpkg.RME_GBRMPA_ID))
    for (sp_idx, icc_csv) in enumerate(icc_csvs)
        order_perm = [ordering_dict[id] for id in icc_csv[:, 1]]
        init_cover[:, :, sp_idx] .= icc_csv[order_perm, 2:end]
    end

    init_cover = dropdims(mean(init_cover, dims=2), dims=2) ./ 100
    species_names = [
        "arborescent Acropora",
        "tabular Acropora",
        "corymbose Acropora",
        "corymbose non-Acropora",
        "Small massives",
        "Large massives"
    ]

    dims = (
        Dim{:species}(species_names),
        Dim{:locations}(canonical_gpkg.UNIQUE_ID)
    )

    savecube(YAXArray(dims, init_cover'), output_path, driver=:netcdf)

    return nothing
end
