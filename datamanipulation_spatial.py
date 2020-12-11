import pandas as pd
import numpy as np

import folium
from folium.features import DivIcon

from sklearn import preprocessing


def standardizeDF(df, measure_name):
    """
        This function takes in a dataframe and creates and adds a column to it with the standardized value
        Therefore, it makes mean = 0 and scales the data to unit variance.
        Input: measure_name : column to be standardized
        
    """
    name = f"{measure_name}_standardized"
    scaler = preprocessing.StandardScaler()
    df[name] = scaler.fit_transform(df[[measure_name]])
    return df


def normalizeDF(df, measure_name, min_range=0, max_range=1):
    """
        This function takes in a dataframe and creates and adds a column to it with the normalized value
         MinMaxScaler scales all the data features in the range [0, 1] or else in the range [-1, 1] 
         if there are negative values in the dataset.
        Input: measure_name : column to be normalized
    """
    name = f"{measure_name}_normalized"
    # Create the Scaler object
    scaler = preprocessing.MinMaxScaler(feature_range=(min_range, max_range))
    df[name] = scaler.fit_transform(df[[measure_name]])
    return df


# Read the data into a dataframe
full_df = pd.read_csv("data\listings_1.csv")

# These are the primary fields we are interested in
def createSpatialData():
    rental_geo_df = full_df[
        [
            "neighbourhood_cleansed",
            "neighbourhood_group_cleansed",
            "latitude",
            "longitude",
            "price",
            "has_availability",
            "accommodates",
        ]
    ].copy()

    glow_color_list = [
        "#befdb7",
        "#1B03A3",
        "#FEFCD7",
        "#a60000",
        "#FE019A",
        "#4d4dff",
        "#ff6ec7",
        "#72c100",
        "#ff073a",
        "#e2ffdc",
        "#c8362e",
        "#f3cc03",
        "#df00fe",
        "#bb9a14",
        "#98a2af",
        "#a2a2a2",
        "#ff3f03",
    ]

    glow_group_color = dict(
        zip(
            list(rental_geo_df.groupby("neighbourhood_group_cleansed").groups.keys()),
            glow_color_list,
        )
    )
    rental_geo_df["glow_marker_color"] = rental_geo_df[
        "neighbourhood_group_cleansed"
    ].map(glow_group_color)

    # Create a new dataframe with average latitude an longitude per neighborhood (88 of these) and Max of the neighborhood group they belong in and max of the marker vcolor
    rental_neighborhood_df = rental_geo_df.groupby(["neighbourhood_cleansed"]).agg(
        {
            "latitude": "mean",
            "longitude": "mean",
            "neighbourhood_group_cleansed": "max",
            "glow_marker_color": "max",
            "neighbourhood_cleansed": "count",
        }
    )

    # Create the Scaler object
    scaler = preprocessing.MinMaxScaler(feature_range=(0, 50))
    rental_neighborhood_df["nbd_count_normalized"] = scaler.fit_transform(
        rental_neighborhood_df[["neighbourhood_cleansed"]]
    )

    # Group the dataframe by neighbourhood groups
    rental_grp_nbd_df = rental_geo_df.groupby(["neighbourhood_group_cleansed"]).agg(
        {
            "latitude": "mean",
            "longitude": "mean",
            "glow_marker_color": "max",
            "neighbourhood_group_cleansed": "count",
        }
    )

    # Create the Scaler object to scale the count of rentals value to between a certain range
    scaler = preprocessing.MinMaxScaler(feature_range=(0, 60))
    rental_grp_nbd_df["nbd_count_normalized"] = scaler.fit_transform(
        rental_grp_nbd_df[["neighbourhood_group_cleansed"]]
    )

    return rental_geo_df, rental_neighborhood_df, rental_grp_nbd_df
