logistic(x) = log((x / (1 - x)) + 0.01)
logit2prob(x) = (exp(x) - 0.01) / (1 + exp(x) - 0.01)

"""
    cyclone_mortality(dpkg_path::String)

DataFrames with windspeed and mortality data for corals (in this order):
- Branching 3 (above depth 5)
- Branching 3 (below depth 5)
- Massives
"""
function cyclone_mortality(dpkg_path::String)::Tuple{Function,Function,Function}
    # Read cyclone mortality csv file
    filepath = joinpath(dpkg_path, "cyclones", "coral_cover_cyclone.csv")
    df = CSV.read(filepath, DataFrame; types=[Int64, Symbol, Float64, Float64])
    df[!, :mortality] .= 0.0

    # Branching 3 (above 5) mortrality
    df_deeper_than_5 = df[(df.morphology.==:branching).&(df.depth.==3), :]
    df_deeper_than_5.mortality .= max.(0 .- (df_deeper_than_5.cover ./ 100), 0)

    # Branching 8 (below 5) mortality
    df_shallower_than_5 = df[(df.morphology.==:branching).&(df.depth.==8), :]
    df_shallower_than_5.mortality .= max.(0 .- (df_shallower_than_5.cover ./ 100), 0)

    # Massive coral mortality
    df_massives = df[df.morphology.==:massive, :]
    df_massives.mortality .= 0 .- (df_massives.cover ./ 100)

    y_deeper_than_5 = branching_regression(df_deeper_than_5[!, [:windspeed, :mortality]])
    y_shallower_than_5 = branching_regression(
        df_shallower_than_5[!, [:windspeed, :mortality]]
    )
    y_massives = massive_regression(df_massives[!, [:windspeed, :mortality]])

    return y_deeper_than_5, y_shallower_than_5, y_massives
end

"""
    branching_regression(df::DataFrame)::Function

Returns prediction function for branching corals.
"""
function branching_regression(df::DataFrame)::Function
    # Apply logistic function
    df[!, :mortality_log] = logistic.(df.mortality)

    # Linear regression
    ols = lm(@formula(mortality_log ~ windspeed), df)
    b, a = coef(ols)

    # Convert back from logistic to prob
    tmx_y(x) = x > 0 ? (exp(a * x + b) - 0.01) / (1 + exp(a * x + b) - 0.01) : 0.0
    return y(x) = min(max(tmx_y(x), 0.0), 1.0)
end

"""
    massive_regression(df::DataFrame)::Function

Returns prediction function for massives.
"""
function massive_regression(df::DataFrame)::Function
    # Adjust linear regressioin
    ols = lm(@formula(mortality ~ windspeed), df)
    b, a = coef(ols)
    tmx_y(x) = x > 0 ? (a * x + b) : 0.0
    return y(x) = min((max(tmx_y(x), 0.0)), 1.0)
end

function mortality_rates(dpkg_path::String)
    # Rows - lower and upper limits for each category (m/s);
    # Cols - categories 0, 1, 2, 3, 4 or 5 (cat. 0 was added to represent no cyclone)
    # Last idx upper limit is 254 km/h (1 min max sustained speed) converted to m/s
    WINDSPEED_RANGES =
        [[0, 0] [17, 24.5] [24.6, 32.5] [32.6, 44.2] [44.2, 55.3] [55.3, 70.5]]

    # This is used when converting cyclone categories into windspeed
    mean_windspeeds = mean(WINDSPEED_RANGES; dims=1)

    # Regression model for each coral_group mortality
    y_deeper_than_5, y_shallower_than_5, y_massives = cyclone_mortality(dpkg_path)

    coral_groups = [:branching_deeper_than_5, :branching_shallower_than_5, :massives]

    axlist = (
        Dim{:cyc_categories}(1:length(mean_windspeeds)), Dim{:coral_groups}(coral_groups)
    )

    data =
        vcat(
            y_deeper_than_5.(mean_windspeeds),
            y_shallower_than_5.(mean_windspeeds),
            y_massives.(mean_windspeeds),
        )'

    return YAXArray(axlist, data)
end
