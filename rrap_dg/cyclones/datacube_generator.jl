using CSV
using DataFrames
using DimensionalData
import GeoDataFrames as GDF
using GLM
using NetCDF
using Statistics
using YAXArrays

include("scenarios.jl")
include("mortality_regression.jl")

function generate(rrapdg_dpkg_path::String, rme_dpkg_path::String, output_path::String)
    # Get yaxarray of coral mortality for each cyclone category and coral_group
    _mortality_rates = mortality_rates(rrapdg_dpkg_path)

    # rrap_dg geodatapackage
    rrap_gdf::DataFrame = _rrap_gdf(rrapdg_dpkg_path)

    # Get YAXArray of cyclone scenarios (in windspeeds) for each reef (from RRAP)
    scens::YAXArray = cyclone_scenarios(rrap_gdf, rme_dpkg_path)

    # Fill scens with mortality rate for each coral group
    massives = contains.(scens.species, "massives")
    massive_mr = collect(_mortality_rates[:, At(:massives)])
    scens[:, :, massives, :] = massive_mr[Int64.(scens[:, :, massives, :].data)]

    branching = .!massives
    branching_deeper_than_mr = collect(_mortality_rates[:, At(:branching_deeper_than_5)])
    locations_deeper_than = rrap_gdf.depth_mean .> 5
    scens[:, locations_deeper_than, branching, :] = branching_deeper_than_mr[Int64.(
        scens[:, locations_deeper_than, branching, :].data
    )]

    branching_shallower_than_mr = collect(
        _mortality_rates[:, At(:branching_shallower_than_5)]
    )
    locations_shallower_than = rrap_gdf.depth_mean .<= 5
    scens[:, locations_shallower_than, branching, :] = branching_shallower_than_mr[Int64.(
        scens[:, locations_shallower_than, branching, :].data
    )]

    filename = joinpath(output_path, "cyclone_mortality.nc")
    return savecube(scens, filename; driver=:netcdf, overwrite=true)
end

function _rrap_gdf(rrapdg_dpkg_path::String)::DataFrame
    rrapdg_dpkg_name = splitpath(rrapdg_dpkg_path)[end]
    cluster_name = split(rrapdg_dpkg_name, '_')[1]
    return GDF.read(joinpath(rrapdg_dpkg_path, "spatial", "$(cluster_name).gpkg"))
end
