using CSV
using DataFrames
using DimensionalData
using YAXArrays
using Statistics

# Last idx upper limit is 254 km/h (1 min max sustained speed) converted to m/s
# Rows - lower and upper limits for each category (m/s); Cols - categories 1, 2, 3, 4 or 5
windspeed_ranges = [[17, 24.5] [24.6, 32.5] [32.6, 44.2] [44.2, 55.3] [55.3, 70.5]]

# This is used when converting cyclone categories into windspeed
mean_windspeeds = mean(windspeed_ranges; dims=1)

function cyclone_scenarios(datapackage_path::String)
    input_folder = joinpath(datapackage_path, "data_files", "cyc_csv")
    scen_files = readdir(input_folder)

    # This is only to determine number of timesteps, locations and location_labels
    tmp_file = CSV.read(
        joinpath(input_folder, scen_files[1]),
        DataFrame;
        stringtype=String,
        header=false,
        comment="#"
    )

    locations = string.(tmp_file[:, 1])

    # First column holds locations indexes and the remaining are timesteps
    n_timesteps = length(tmp_file[1, 2:end])
    n_scenarios = length(scen_files)
    n_locations = length(locations)

    axlist = (
        Dim{:timesteps}(1:n_timesteps),
        Dim{:scenarios}(1:n_scenarios),
        Dim{:locations}(string.(locations)),
    )

    scenarios = YAXArray(axlist, zeros(n_timesteps, n_scenarios, n_locations))#, n_cgroups))

    types = vcat(String, fill(Int64, n_timesteps))

    # Each file is a scenario
    for (idx_s, file) in enumerate(scen_files)
        scenario = scenarios[scenarios=At(idx_s)]
        filepath = joinpath(input_folder, file)
        df = CSV.read(filepath, DataFrame; types=types, header=false, comment="#")

        category_scenarios = Matrix(df[:, 2:end])'

        scenario .= map(x -> x > 0 ? mean_windspeeds[x] : x, category_scenarios)
    end

    return scenarios
end
