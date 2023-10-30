using YAXArrays
using NetCDF
import GeoDataFrames as GDF

include("scenarios.jl")
include("mortality_regression.jl")

function generate(rrapdg_dpkg_path::String, rme_dpkg_path::String, output_path::String)
    # Get dataframe with windspeed versus mortality (from C~Scape/Fabricius2008)
    y_b3, y_b8, y_m = cyclone_mortality(rrapdg_dpkg_path)

    # Get YAXArray of cyclone scenarios (in windspeeds) for each reef (from RRAP)
    reef_ids::Vector{String} = filter_reef_ids(rrapdg_dpkg_path, rme_dpkg_path)
    scens = cyclone_scenarios(rme_dpkg_path, reef_ids)

    # Apply all regressions for each scenario/location to estimate coral mortality
    scens_b3 = map(x -> x > 0.0 ? y_b3(x) : 0.0, scens)
    scens_b8 = map(x -> x > 0.0 ? y_b8(x) : 0.0, scens)
    scens_m = map(x -> x > 0.0 ? y_m(x) : 0.0, scens)

    # Coral Groups
    cgroups = (["branch3", "branch8", "massive"])

    # Generate datacube with estimate mortality for each timestep/scenario/location (reef)/ coral group
    cube = concatenatecubes([scens_b3, scens_b8, scens_m], Dim{:cgroups}(cgroups))

    # Save datacube as NetCDF file
    filename = joinpath(output_path, "cyclones_mortality.nc")
    return savecube(cube, filename; driver=:netcdf, overwrite=true)
end

function filter_reef_ids(rrapdg_dpkg_path::String, rme_dpkg_path::String)::Vector{String}
    rrapdg_dpkg_name = split(rrapdg_dpkg_path, '/')[end]
    small_reef_name = split(rrapdg_dpkg_name, '_')[1]

    small_reef_path = joinpath(rrapdg_dpkg_path, "spatial", "$(small_reef_name).gpkg")
    small_gdf = GDF.read(small_reef_path)

    large_reef_path = joinpath(rme_dpkg_path, "data_files", "region", "reefmod_gbr.gpkg")
    large_gdf = GDF.read(large_reef_path)

    match_ids = unique(
        vcat(
            [findall(GDF.intersects.(large_gdf.geom, [geom])) for geom in small_gdf.geom]...
        ),
    )

    return large_gdf[match_ids, "LABEL_ID"]
end
