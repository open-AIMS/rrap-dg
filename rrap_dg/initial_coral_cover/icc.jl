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
    bin_edges()

Helper function defining coral colony diameter bin edges in cm.
"""
function bin_edges()
    return Matrix([
        0.0 0.0 0.0 0.0 0.0 0.0 0.0;          #  arborescent Acropora
        5.0 7.5 10.0 20.0 40.0 100.0 150.0;   #  tabular Acropora
        5.0 7.5 10.0 20.0 35.0 50.0 100.0;    #  corymbose Acropora
        5.0 7.5 10.0 15.0 20.0 40.0 50.0;     #  corymbose non-Acropora and Pocillopora
        5.0 7.5 10.0 20.0 40.0 50.0 100.0;    #  small massives
        5.0 7.5 10.0 20.0 40.0 50.0 100.0     #  large massives
    ])
end

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

    if isdir(joinpath(dpkg_path, "data_files"))
        # ReefMod or RME dataset
        return joinpath(dpkg_path, "data_files", "initial")
    end

    error("Unknown directory structure.")
end


"""
    load_gbr_gpkg(data_path::String, site_data::DataFrame)::YAXArray

Load GBR geopackage associated with RME (v1.0.x) with precomputed/packaged area and
\$k\$ values.

# Arguments
- `rrapdg_dpkg` : Path to rrap-dg data package

# Returns
YAXArray[locs, species]
"""
function load_gbr_gpkg(data_dir::String)
    id_list = CSV.read(
        joinpath(_get_id_dir(data_dir), "id_list_2023_03_30.csv"),
        DataFrame;
        header=false,
        comment="#",
    )

    # Re-order spatial data to match RME dataset
    # MANUAL CORRECTION
    gbr_data = GDF.read(_get_gbr_gpkg(data_dir))

    try
        gbr_data[gbr_data.LABEL_ID .== "20198", :LABEL_ID] .= "20-198"
    catch
        gbr_data[gbr_data.RME_GBRMPA_ID .== "20198", :RME_GBRMPA_ID] .= "20-198"
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
    load_rme_cover(rrapdg_dpkg::String, gbr_gpkg::DataFrame)::YAXArray

Load mean of initial covers from ReefMod Engine datasets (v1.0.18).

# Arguments
- `rrapdg_dpkg` : Path to ReefMod data
- `gbr_gpkg` : ReefMod GBR-scale geopackage
- `bin_edges` : Bin edges for each functional group and size class

# Returns
YAXArray[locs, species]
"""
function load_rme_cover(
    dataset::String,
    gbr_gpkg::DataFrame,
    bin_edges::Matrix{Float64}
)::YAXArray
    icc_path = _get_icc_dir(dataset)

    # Identify coral cover files with known prefix pattern
    valid_files = filter(isfile, readdir(icc_path; join=true))
    icc_files = filter(x -> occursin("coral_", basename(x)), valid_files)
    if isempty(icc_files)
        ArgumentError("No coral cover data files found in: $(icc_path)")
    end
    @assert length(icc_files) == 6 "Number of coral files do not match expected number of species (6)"

    # Shape is locations, scenarios, species
    # 20 is the known number of scenarios.
    loc_ids = try
        gbr_gpkg.LABEL_ID
    catch
        gbr_gpkg.RME_LABEL_ID
    end
    icc_data = zeros(length(loc_ids), 20, length(icc_files))
    for (i, fn) in enumerate(icc_files)
        icc_data[:, :, i] = Matrix(
            CSV.read(fn, DataFrame; drop=[1], header=false, comment="#")
        )
    end

    # Use ReefMod distribution for coral size class population (shape parameters have units
    # log(cm^2)) as suggested by YM (pers comm. 2023-08-08 12:55pm AEST).
    # Distribution is used to split ReefMod initial species covers into ADRIA's 6 size
    # classes by weighting with the cdf.
    reef_mod_area_dist = LogNormal(log(700), log(4))
    bin_edges_area = _colony_mean_area(bin_edges)

    # Find integral density between bounds of each size class areas to create weights for each size class.
    cdf_integral = cdf.(reef_mod_area_dist, bin_edges_area)
    size_class_weights = (cdf_integral[:, 2:end] .- cdf_integral[:, 1:(end - 1)])
    size_class_weights = size_class_weights ./ sum(size_class_weights, dims=2)
    replace!(size_class_weights, NaN=>0.0)

    # Take the mean over repeats, as suggested by YM (pers comm. 2023-02-27 12:40pm AEDT).
    # Convert from percent to relative values.
    icc_data = ((dropdims(mean(icc_data; dims=2); dims=2)) ./ 100.0)

    # Repeat species over each size class and reshape to give ADRIA compatible size (36 * n_locs).
    # Multiply by size class weights to give initial cover distribution over each size class.
    icc = Matrix(vcat([stack(icc_data[:, i] .* [size_class_weights[i, :]]) for i in axes(size_class_weights, 1)]...))

    # Convert values relative to absolute area to values relative to k area
    icc = _convert_abs_to_k(icc, gbr_gpkg)

    return YAXArray(
        (
            Dim{:species}(1:(length(icc_files) * 6)),
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
- `init_cc` : Initial coral cover data (relative to k area) to downscale
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
    n_classes = 6
    taxa_names = [
        "arborescent Acropora",
        "tabular Acropora",
        "corymbose Acropora",
        "corymbose non-Acropora",
        "Small massives",
        "Large massives"
    ]

    tn = repeat(taxa_names; inner=n_classes)
    taxa_id = repeat(1:n_classes; inner=n_classes)
    class_id = repeat(1:n_classes, n_classes)
    coral_id = String[join(x, "_") for x in zip(tn, taxa_id, class_id)]

    src_labels = large_ds[match_ids, :LABEL_ID]
    target_names = unique(small_ds.Reef .|> lowercase)

    # Create storage matrix
    n_species = size(init_cc, :species)
    n_locs = length(small_ds.reef_siteid)
    target_init_cover = YAXArray(
        (
            Dim{:species}(coral_id),
            Dim{:locations}(small_ds.reef_siteid)
        ),
        zeros(n_species, n_locs)
    )

    cluster_abs_k_area = (small_ds.k .* small_ds.area)'
    has_capacity = vec(cluster_abs_k_area .> 0.0)

    for target_name in target_names
        matching_locs = contains.(target_names, target_name)
        label = src_labels[matching_locs]

        cluster_cover = dropdims(sum(init_cc[locs=At(label)], dims=2), dims=2)

        # Match up locations based on order indicated by geospatial dataset
        is_target = ((small_ds.Reef .|> lowercase) .== target_name)
        relevant_locs = is_target .& has_capacity

        # Get cover relative to cluster's absolute area
        # Only use relevant locations to avoid zero-division and speed up calculations.
        target_init_cover[:, relevant_locs] .= (
            (cluster_cover .* cluster_abs_k_area[:, relevant_locs])
            ./
            cluster_abs_k_area[:, relevant_locs]
        )
    end

    # Sum of species/size class cover should be <= maximum carrying capacity
    @assert all(sum(target_init_cover, dims=1) .<= cluster_abs_k_area)

    return target_init_cover
end

"""
    downscale_icc(rme_dataset::String, target_gpkg::String, output_path::String)::Nothing

Downscale initial coral covers from ReefMod Engine for a given spatial area and export to
provided output path.

# Arguments
- `rme_dataset` : Path to rrap-dg data package
- `target_gpkg` : Path to geopackage file defining area of interest
- `output_path` : Path to export to resulting netCDF to
"""
function downscale_icc(dataset::String, target_gpkg::String, output_path::String; bin_edges=bin_edges())::Nothing
    gbr_gpkg = load_gbr_gpkg(dataset)
    rme_icc = load_rme_cover(dataset, gbr_gpkg, bin_edges())
    target_gpkg = GDF.read(target_gpkg)

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
    downscale_icc(rme_dataset::String, target_gpkg::String, output_path::String)::Nothing

Downscale initial coral covers from ReefMod Engine for a given spatial area and export to
provided output path.

# Arguments
- `rme_dataset` : Path to rrap-dg data package
- `target_gpkg` : Path to geopackage file defining area of interest
- `output_path` : Directory to export the resulting netCDFs to
- `bin_edge_fn` : TOML file defining bin edges
"""
function downscale_icc(dataset::String, target_gpkg::String, output_path::String, bin_edge_fn::String)::Nothing
    gbr_gpkg = load_gbr_gpkg(dataset)
    target_gpkg = GDF.read(target_gpkg)

    @assert isdir(output_path) "$(output_path) is not a valid directory."

    defined_bin_edges = TOML.parsefile(bin_edge_fn)
    for (k, v) in defined_bin_edges
        rme_icc = load_rme_cover(dataset, gbr_gpkg, Matrix(stack(v)'))
        icc = downscale_icc(rme_icc, gbr_gpkg, target_gpkg)
        try
            savecube(icc, joinpath(output_path, "$(k).nc"), driver=:netcdf)
        catch err
            if err isa ArgumentError
                @info "File appears to already exist or cannot be written to."
            end
        end
    end

    return nothing
end