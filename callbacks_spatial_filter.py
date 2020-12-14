import pandas as pd
import numpy as np

import folium
from folium.features import DivIcon

from datamanipulation_spatial_filter import *

# Dataframes available to all functions
rental_geo_df, rental_neighborhood_df, rental_grp_nbd_df = createSpatialData()


def createRentalMap(df, fixed_radius, nbd_or_grp):
    """
    This function tkes in a dataframe and applies a fucntion that creates circle markers for every 
        latitude and longitude in the dataframe

    Args:
        df ([dataframe]): [Dataframe containing latitude and longitude as well as column nbd_count_normalized
                            for count of listings normalized ]
        fixed_radius ([boolean]): [if true use 30 as fixed radius, if false use the count to determine size of circle]
        nbd_or_grp ([String]): [neighbourhood/group]

    Returns:
        [Folium Map]: [Folium map]
    """
    # Initialize a Folium map. Center it to the mean of latitude and longitude of the entire dataset
    this_map = folium.Map(
        location=[df["latitude"].mean(), df["longitude"].mean()],
        tiles="CartoDB positron",
        zoom_start=13,
    )

    def plotDot(point_row, fixed_radius, nbd_or_grp):
        """
            This function adds elements to this_map. It adds CircleMarkers with fixed or varying radius
            It also creates circles with tooltips
            A text indicating the count is added close to the circle

            Args : point_row - a row of data expected to contain following columns 
                            a) latitude
                            b) longitude
                            c) neighbourhood_cleansed or neighbourhood_group_cleansed
                            d) glow_marker_color

            Returns : Folium map with circles added                    

        """

        if fixed_radius:
            radius = 30
        else:
            radius = point_row["nbd_count_normalized"]

        if nbd_or_grp == "neighbourhood":
            text = f'{point_row["neighbourhood_cleansed"]}'
        else:
            text = f'{point_row["neighbourhood_group_cleansed"]}'

        folium.CircleMarker(
            location=[point_row["latitude"], point_row["longitude"]],
            radius=radius,
            weight=3,
            color=point_row["glow_marker_color"],
            fill_color=point_row["glow_marker_color"],
            fill_opacity=0.7,
        ).add_child(folium.Tooltip(f"{point_row.name}: {text}")).add_to(this_map)

        # Add text of count within circle
        folium.map.Marker(
            [point_row["latitude"], point_row["longitude"]],
            icon=DivIcon(
                icon_size=(150, 36),
                icon_anchor=(0, 0),
                html='<div style="font-size: 9pt font-weight:bold">%s</div>' % text,
            ),
        ).add_to(this_map)
        return

    # Create circle markers for every listing by applying the plotDot function
    if nbd_or_grp == "neighbourhood":
        df[
            [
                "latitude",
                "longitude",
                "glow_marker_color",
                "nbd_count_normalized",
                "neighbourhood_cleansed",
            ]
        ].apply(plotDot, args=(fixed_radius, nbd_or_grp), axis=1)
    else:
        df[
            [
                "latitude",
                "longitude",
                "glow_marker_color",
                "nbd_count_normalized",
                "neighbourhood_group_cleansed",
            ]
        ].apply(plotDot, args=(fixed_radius, nbd_or_grp), axis=1)
    return this_map


def createListingSpatial(rental_geo_df):
    this_map = folium.Map(
        location=[rental_geo_df["latitude"].mean(), rental_geo_df["longitude"].mean()],
        tiles="cartodbdark_matter",
        zoom_start=13,
    )

    def plotDot(point_row):
        is_available = "Yes" if point_row["has_availability"] == "t" else "No"

        text = f'Neighborhood: {point_row["neighbourhood_cleansed"]}<br>Is available: {is_available}<br>Accommodates: {point_row["accommodates"]}<br>Rent: {point_row["price"]}'
        folium.CircleMarker(
            location=[point_row["latitude"], point_row["longitude"]],
            radius=1,
            weight=2,
            color=point_row["glow_marker_color"],
            fill_opacity=0.7,
        ).add_child(folium.Tooltip(f"{text}")).add_to(this_map)
        return

    rental_geo_df[
        [
            "latitude",
            "longitude",
            "neighbourhood_cleansed",
            "glow_marker_color",
            "has_availability",
            "accommodates",
            "price",
        ]
    ].apply(plotDot, axis=1)
    return this_map


def saveNeighborhoodMapHTML(nbd):
    """
    Call this function to create the HTML of the neighborhood map
    Input : Neighborhood group 
    Returns : a filename of the folium map created and saved 
    """
    # TBD Add an all and then use All or nbd to filter the dataframe
    if nbd == "All":
        filtered_df = rental_neighborhood_df.copy()
    else:
        filtered_df = rental_neighborhood_df[
            rental_neighborhood_df["neighbourhood_group_cleansed"] == nbd
        ].copy()
    this_map = createRentalMap(filtered_df, False, "neighbourhood")
    filename = (
        "assets/Maps/NeighborhoodCountMap.html"
        if nbd == "All"
        else f"assets/Maps/NeighborhoodCountMap-{nbd}.html"
    )
    this_map.save(filename)
    return filename


def saveListingMapHTML(nbd):
    """
        Call this function to create the HTML of the individual listings  map
        Input : Neighborhood group 
        Returns : a filename of the folium map created and saved 
    """
    # TBD Add an all and then use All or nbd to filter the dataframe (create a copy of it)
    if nbd == "All":
        filtered_df = rental_geo_df.copy()
    else:
        filtered_df = rental_geo_df[
            rental_geo_df["neighbourhood_group_cleansed"] == nbd
        ].copy()

    this_map = createListingSpatial(filtered_df)

    filename = (
        "assets/Maps/IndvListingsMap.html"
        if nbd == "All"
        else f"assets/Maps/IndvListingsMap-{nbd}.html"
    )
    this_map.save(filename)
    return filename


def getNumNbds(nbd):
    """
        Call this function to get number of neighborhooods in a neighborhood group
        Input : Neighborhood group 
        Returns : Number of neighborhoods in group
    """
    if nbd == "All":
        filtered_df = rental_geo_df.copy()
    else:
        filtered_df = rental_geo_df[
            rental_geo_df["neighbourhood_group_cleansed"] == nbd
        ].copy()

    # Return the number of unique neighborhoods in the group
    return filtered_df["neighbourhood_cleansed"].unique().size


def getAvgPriceNbd(nbd):
    """
        Call this function to get average price(rent) in the neighborhood group
        Input : Neighborhood group 
        Returns : Average price  of listings in neighborhood group
    """
    # TBD Add an all and then use All or nbd to filter the dataframe (create a copy of it)
    if nbd == "All":
        filtered_df = rental_geo_df.copy()
    else:
        filtered_df = rental_geo_df[
            rental_geo_df["neighbourhood_group_cleansed"] == nbd
        ].copy()

    # Ignore the NaNs when calculating the mean
    return np.round(np.nanmean(rental_geo_df["price"]), 2)


def getAvailableListingsNum(nbd):
    """
        Call this function to get the number of available listings in the neighborhood group
        Input : Neighborhood group 
        Returns : Number of available listings in neighborhood group
    """
    # TBD Add an all and then use All or nbd to filter the dataframe (create a copy of it)
    if nbd == "All":
        filtered_df = rental_geo_df.copy()
    else:
        filtered_df = rental_geo_df[
            rental_geo_df["neighbourhood_group_cleansed"] == nbd
        ].copy()

    # Ignore the NaNs when calculating the mean
    return filtered_df[filtered_df["has_availability"] == 1].shape[0]

