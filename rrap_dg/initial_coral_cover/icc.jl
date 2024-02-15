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
    YAXArrays

using
    Distributions,
    Statistics

import GeoDataFrames as GDF
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
    load_rme_gpkg(data_path::String, site_data::DataFrame)::YAXArray

Load GBR geopackage associated with RME (v1.0.18) with precomputed/packaged area and
\$k\$ values.

# Arguments
- `rrapdg_dpkg` : Path to rrap-dg data package

# Returns
YAXArray[locs, species]
"""
function load_rme_gpkg(rrapdg_dpkg::String)
    id_list = CSV.read(
        joinpath(rrapdg_dpkg, "spatial", "id_list_2023_03_30.csv"),
        DataFrame;
        header=false,
        comment="#",
    )

    # Re-order spatial data to match RME dataset
    # MANUAL CORRECTION
    gbr_data = GDF.read(joinpath(rrapdg_dpkg, "spatial", "reefmod_gbr.gpkg"))
    gbr_data[gbr_data.LABEL_ID .== "20198", :LABEL_ID] .= "20-198"
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

# Returns
YAXArray[locs, species]
"""
function load_rme_cover(rrapdg_dpkg::String, gbr_gpkg::DataFrame)::YAXArray
    icc_path = joinpath(rrapdg_dpkg, "coral_cover")

    # Identify coral cover files with known prefix pattern
    valid_files = filter(isfile, readdir(icc_path; join=true))
    icc_files = filter(x -> occursin("coral_", basename(x)), valid_files)
    if isempty(icc_files)
        ArgumentError("No coral cover data files found in: $(icc_path)")
    end
    @assert length(icc_files) == 6 "Number of coral files do not match expected number of species (6)"

    # Shape is locations, scenarios, species
    # 20 is the known number of scenarios.
    loc_ids = gbr_gpkg.LABEL_ID
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
    bin_edges_area = _colony_mean_area(Float64[0, 2, 5, 10, 20, 40, 80])

    # Find integral density between bounds of each size class areas to create weights for each size class.
    cdf_integral = cdf.(reef_mod_area_dist, bin_edges_area)
    size_class_weights = (cdf_integral[2:end] .- cdf_integral[1:(end - 1)])
    size_class_weights = size_class_weights ./ sum(size_class_weights)

    # Take the mean over repeats, as suggested by YM (pers comm. 2023-02-27 12:40pm AEDT).
    # Convert from percent to relative values.
    icc_data = ((dropdims(mean(icc_data; dims=2); dims=2)) ./ 100.0)
    # icc_data ./= 100.0

    # Repeat species over each size class and reshape to give ADRIA compatible size (36 * n_locs).
    # Multiply by size class weights to give initial cover distribution over each size class.
    # icc = zeros(36, length(loc_ids), 20)
    # for scen in axes(icc_data, 2)
    #     icc[:, :, scen] .= Matrix(hcat(reduce.(vcat, eachrow(icc_data[:, scen, :] .* [size_class_weights]))...))
    # end
    icc_data = Matrix(hcat(reduce.(vcat, eachrow(icc_data .* [size_class_weights]))...))

    # Convert values relative to absolute area to values relative to k area
    icc_data = _convert_abs_to_k(icc_data, gbr_gpkg)

    return YAXArray(
        (
            Dim{:species}(1:(length(icc_files) * 6)),
            Dim{:locs}(loc_ids)
            # Dim{:scenarios}(1:20)
        ),
        icc_data
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
Cover for each coral species/size class for each location [species ⋅ location]


    downscale_icc(rrapdg_dpkg::String, output_path::String)::Nothing

Downscale initial coral covers from ReefMod Engine and export to provided output path.

# Arguments
- `rrapdg_dpkg` : Path to rrap-dg data package
- `output_path` : Path to export to resulting netCDF to
"""
function downscale_icc(
    init_cc::YAXArray,
    large_ds::DataFrame,
    small_ds::DataFrame
)::YAXArray
    # Find locations in larger spatial dataset that intersect with smaller dataset
    # TODO: Constrain search to just the area represented by the smaller domain.
    #       Currently this loops over all locations, many of which will be outside
    #       the target area.
    match_ids = unique(
        vcat([findall(GDF.intersects(large_ds.geom, [g])) for g in small_ds.geom]...)
    )

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
            Dim{:reef_siteid}(small_ds.reef_siteid)
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
            small_ds.area[relevant_locs]'
        )
    end

    # Sum of species/size class cover should be <= maximum carrying capacity
    @assert all(sum(target_init_cover, dims=1) .<= small_ds.k')

    return target_init_cover
end
function downscale_icc(rrapdg_dpkg::String, target_cluster::String, output_path::String)::Nothing
    rme_gpkg = load_rme_gpkg(rrapdg_dpkg)
    rme_icc = load_rme_cover(rrapdg_dpkg, rme_gpkg)

    target_gpkg = GDF.read(joinpath(rrapdg_dpkg, "spatial", "$(target_cluster).gpkg"))

    icc = downscale_icc(rme_icc, rme_gpkg, target_gpkg)

    savecube(icc, output_path, driver=:netcdf)

    return nothing
end

# """
#     export_icc(fp::String, icc::NamedDimsArray)::Nothing

# Helper function to export initial coral covers.

# # Arguments
# - `fp` : path to file to write data to.
# - `icc` : initial coral cover data
# """
# function export_icc(fp::String, icc::NamedDimsArray)::Nothing
#     local ds::NCDataset = Dataset(fp, "c")
#     try
#         defDim(ds, "reef_siteid", size(icc, 2))
#         defDim(ds, "species", size(icc, 1))
#         reef_siteid = defVar(ds, "reef_siteid", String, ("reef_siteid",))
#         reef_siteid[:] .= axiskeys(icc, :sites)
#         covers = defVar(ds, "covers", Float32, ("species", "reef_siteid"))
#         covers[:, :] .= icc
#         close(ds)
#     catch
#         # Close handle if any error occurs, otherwise it will remain open and cause issues!
#         close(ds)
#     end

#     return nothing
# end
