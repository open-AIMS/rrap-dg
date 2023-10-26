using YAXArrays
using NetCDF

include("scenarios.jl")
include("mortality_regression.jl")

function generate(
    rrapdg_datapackage_path::String, rme_datapackage_path::String, output_path::String
)
    # Get dataframe with windspeed versus mortality (from C~Scape/Fabricius2008)
    y_b3, y_b8, y_m = cyclone_mortality(rrapdg_datapackage_path)

    # Get YAXArray of cyclone scenarios (in windspeeds) for each reef (from RRAP)
    scens = cyclone_scenarios(rme_datapackage_path)

    # Apply all regressions for each scenario/location to estimate coral mortality
    scens_b3 = map(x -> x > 0.0 ? y_b3(x) : 0.0, scens)
    scens_b8 = map(x -> x > 0.0 ? y_b8(x) : 0.0, scens)
    scens_m = map(x -> x > 0.0 ? y_m(x) : 0.0, scens)

    # Coral Groups
    cgroups = string.([:branch3, :branch8, :massive])

    # Generate datacube with estimate mortality for each timestep/scenario/location (reef)/ coral group
    cube = concatenatecubes([scens_b3, scens_b8, scens_m], Dim{:cgroups}(cgroups))

    # Save datacube as NetCDF file
    filename = joinpath(output_path, "cyclone_mortality.nd")
    savecube(cube, filename; driver=:netcdf, overwrite=true)
end
