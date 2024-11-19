from typing import Sequence

import numpy as np
import xarray as xr

from scipy.stats import genextreme as gev
from scipy.stats import norm
from scipy.optimize import curve_fit
from shapely.geometry import Polygon, Point


def gauss(x, amp, mu, sigma):
    """Gaussian function.

    Equivalent to 'gauss1' option for MATLAB's `fit()`.

    References
    ----------
    - https://au.mathworks.com/help/curvefit/list-of-library-models-for-curve-and-surface-fitting.html
    """
    return amp * np.exp(-(((x - mu) / sigma) ** 2))


def fit_gauss(x, y):
    """Fit a gaussian curve and return optimal parameters.

    Args:
        x: time
        y: data

    Returns:
        tuple[float, float, float]: amplitude, mean, standard deviation.
            Optimal values for the parameters so that the sum of the squared
            residuals of f(xdata, *popt) - ydata is minimized.
    """
    # Create an initial guess
    mu, sigma = norm.fit(y)
    init_guess = (1, mu, sigma)  # amplitude, mean, std

    # Note: `curve_fit` does not work if `x` is passed in directly.
    popt, _ = curve_fit(gauss, range(0, len(x)), y, p0=init_guess)
    return popt


def inpoly(reef_lon, reef_lat, cluster_lonlats):
    """Returns index of GBR location that overlaps the cluster."""
    poly = Polygon(cluster_lonlats)
    inds = np.array(
        [
            1 if poly.intersects(Point(*lon_lat)) else 0
            for lon_lat in zip(reef_lon, reef_lat)
        ]
    )

    return np.where(inds == 1)[0]


def get_closest_data(
    target_site: tuple, lonlats: np.array, dhw: xr.DataArray
) -> xr.Dataset:
    """Get data closest to the target site."""
    # Use sum of absolute differences to determine closeness
    box_shape = dhw.shape
    if len(box_shape) > 2:
        # ignore the time dimension
        box_shape = dhw.shape[1:]

    ind = np.unravel_index(
        np.argmin(np.abs(lonlats - target_site).sum(axis=1)), box_shape
    )

    # Handle datasets with time dimension
    if len(dhw.shape) > 2:
        # WARNING: requires >3.11 Python
        return dhw[:, *ind].to_dataset(name="CRS_DHW")

    # WARNING: requires >3.11 Python
    return dhw[*ind].to_dataset(name="CRS_DHW")


def extract_DHW_pattern(recom_files: Sequence[str]):
    """Extract mean DHW pattern using RECOM multi-marine heat wave years data.

    The full cluster spatial average is taken from the RECOM pattern.
    For each site, the closest grid cell DHW pattern variation from the mean is taken.

    Args:
        recom_files (list[str]): List of file locations for RECOM data in netCDF format.

    Returns:
        tuple[np.array, np.array, np.array, np.array]:
            dhw_pattern, mean_dhw_pattern, cluster_lon, cluster_lat.
    """
    n_files = len(recom_files)
    with xr.open_dataset(recom_files[0]) as nc:
        dhw_pattern = nc["dhw0"].squeeze()
        lons = nc["x_centre"].values.squeeze()
        lats = nc["y_centre"].values.squeeze()

    for rf in recom_files[1:]:
        with xr.open_dataset(rf) as nc:
            dhw_pattern += nc["dhw0"].squeeze()

    dhw_pattern /= n_files  # mean over time
    mean_dhw_pattern = np.nanmean(dhw_pattern)  # mean of domain

    return dhw_pattern, mean_dhw_pattern, lons, lats


def create_max_DHW(
    hist_dhw: xr.Dataset,
    proj_dhw: xr.Dataset,
    proj_range: Sequence[int],
):
    """Extract and concatenate maximum yearly DHW for a given location.

    Extracts historic data and concatenates with projected data for a
    specified projection time frame.

    Args:
        cluster_dhw: Historic DHW data for cluster.
        proj_cluster_dhw: Projected DHW data (e.g., MIROC5).
        proj_range: Year range of projected data (end exclusive).

    Returns:
        tuple[np.array, np.array, np.array]:
            - Historic max DHW for location.
            - Timeframe.
            - Combined max DHW across hist/projected time periods.
    """
    # Find max historical DHW by grouping each unique year and getting the max
    hist_max_DHW = (
        hist_dhw.groupby("time.year").max(dim=...).to_array().values.squeeze()
    )

    # Concatenate the data in a single array
    time_yr = np.unique(hist_dhw.time.dt.year.data)
    total_timeframe = np.concatenate((time_yr, list(range(*proj_range))))
    all_dhw_data = np.concatenate((hist_max_DHW, proj_dhw))

    return hist_max_DHW, total_timeframe, all_dhw_data


def detrended_max_DHW(
    mean_hist_dhw: xr.Dataset,
    mean_proj_dhw: np.array,
    gen_year_tf: Sequence[int],
    proj_range: tuple[int],
):
    """Retrieve the detrended DHW distribution for a given location.

    Args:
        mean_hist_dhw: Historic DHW data.
        mean_proj_dhw: Projected DHW data (e.g., MIROC5).
        gen_year_tf: Years of interest (to generate data for).
        proj_range: Year range of simulated projections (e.g., MIROC5).

    Returns:
        tuple: dens_prob, max_DHW_detrend
            - Generalized Extreme Value probability.
            - Detrended maximum DHW.
    """
    hist_max_DHW, dhw_timeframe, combined_dhw_data = create_max_DHW(
        mean_hist_dhw, mean_proj_dhw, proj_range
    )

    popt = fit_gauss(dhw_timeframe, combined_dhw_data)

    # Detrend the DHW for the whole timeseries of available data (CRW and MIROC5)
    data_detrend = combined_dhw_data - gauss(dhw_timeframe, *popt)

    # Put all the historical data plus all years of MIROC5 up to each year
    # from 2025 to 2099
    n_years = len(gen_year_tf)
    max_DHW_detrend = np.zeros((len(dhw_timeframe), n_years))

    dens_prob = list(np.zeros(n_years))
    n_hist_years = len(hist_max_DHW)
    for i in range(n_years):
        # Take all the MIROC5 data <= to the current year and all the CRW data
        # to build a time evolving distribution
        nyearsMIROC5 = gen_year_tf[i] - proj_range[0] + 1
        ub = n_hist_years + nyearsMIROC5

        d_i = data_detrend[0:ub]
        max_DHW_detrend[0:ub, i] = d_i

        # Fit a distribution over these maxDHW using
        # Generalized Extreme Value distribution fitting
        # fix the loc and scale
        # (results in a very poor fit otherwise!)
        # dens_prob[i] = gev.fit(d_i, floc=np.mean(d_i), fscale=np.std(d_i))
        # if i == n_years - 1:
        #     breakpoint()
        # dens_prob[i] = gev.fit(d_i, floc=2, fscale=1.0)

        # Use last few years for estimate
        # dens_prob[i] = gev.fit(d_i, floc=np.mean(d_i[:-30]), fscale=1.1)
        # floc=np.mean(d_i[:-20]), fscale=1.1, f0=-0.2
        dens_prob[i] = gev.fit(d_i, f0=-0.6)

    return dens_prob, max_DHW_detrend
