using DataFrames
using CSV
using GLM

logistic(x) = log((x / (1 - x)) + 0.01)
logit2prob(x) = (exp(x) - 0.01) / (1 + exp(x) - 0.01)

"""
    cyclone_mortality(datapackage_path::String)

DataFrames with windspeed and mortality data for corals (in this order):
- Branching 3 (above depth 5)
- Branching 3 (below depth 5)
- Massive
"""
function cyclone_mortality(datapackage_path::String)::Tuple{Function,Function,Function}
    # Read cyclone mortality csv file
    filepath = joinpath(datapackage_path, "cyclone_mortality", "fabricius2008.csv")
    df = CSV.read(filepath, DataFrame; types=[Int64, Symbol, Float64, Float64])
    df[!, :mortality] .= 0.0

    # Branching 3 (above 5) mortrality
    df_b3 = df[(df.morphology.==:branching).&(df.depth.==3), :]
    df_b3.mortality .= max.(0 .- (df_b3.cover ./ 100), 0)

    # Branching 8 (below 5) mortality
    df_b8 = df[(df.morphology.==:branching).&(df.depth.==8), :]
    df_b8.mortality .= max.(0 .- (df_b8.cover ./ 100), 0)

    # Massive coral mortality
    df_m = df[df.morphology.==:massive, :]
    df_m.mortality .= 0 .- (df_m.cover ./ 100)

    y_b3 = branching_regression(df_b3[!, [:windspeed, :mortality]])
    y_b8 = branching_regression(df_b8[!, [:windspeed, :mortality]])
    y_m = massive_regression(df_m[!, [:windspeed, :mortality]])

    return y_b3, y_b8, y_m
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
    return y(x) = (exp(a * x + b) - 0.01) / (1 + exp(a * x + b) - 0.01)
end

"""
    massive_regression(df::DataFrame)::Function

Returns prediction function for massives.
"""
function massive_regression(df::DataFrame)::Function
    # Adjust linear regressioin
    ols = lm(@formula(mortality ~ windspeed), df)
    b, a = coef(ols)
    return y(x) = a * x + b
end
