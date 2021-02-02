import pandas as pd
import numpy as np

import folium
from folium.features import DivIcon

import plotly.graph_objs as go
import plotly.express as px

# Theme settings
import plotly.io as plt_io


from datamanipulation_bar_sankey import *


dashboard_colors = {
    "superdark-blue": "rgb(31,38,42)",
    "acid-pink": "rgb(213, 3, 160)",
    "black": "rgb(0, 0, 0)",
    "dark-blue-grey": "rgb(103, 117, 126)",
    "medium-blue-grey": "rgb(59,139,235)",
    "dark-blue": "rgb(0,0,0)",
    "superdark-blue": "rgb(31,38,42)",
    "medium-green": "rgb(2,119,189)",
    "light-green": "rgb(245,252,255)",  # This is filter background
    "pink-red": "rgb(178,56,80)",
    "dark-pink-red": "rgb(255, 10, 255)",
    "white": "rgb(251, 251, 252)",
    "light-grey": "rgb(208, 206, 206)",
    "superlight-blue": "rgb(242,242,242)",
    "crimson": "rgb(171, 39, 79)",
    "orange": "rgb(255, 126, 0)",
    "acid-green": "rgb(57, 255, 20)",
}
# A Pastel color list choice
full_color_list = [
    "#f3d1dc",
    "#f6a7c1",
    "#fcf0cf",
    "#fdcf76",
    "#ffabab",
    "#89aeb2",
    "#97f2f3",
    "#f1e0b0",
    "#f1cdb0",
    "#e7cfc8",
    "#ecad8f",
    "#c1cd97",
    "#38908f",
    "#b2ebe0",
    "#ffbfa3",
    "#e08963",
    "#9dabdd",
    "#e7ffac",
    "#bffcc6",
    "#877111",
    "#b57fb3",
    "#ffb347",
    "#ff6961",
    "#aec6cf",
]

###############################################################################################################################
# Dataframes available to all functions
###############################################################################################################################
(
    rental_df,
    rental_geo_df,
    rental_neighborhood_df,
    rental_grp_nbd_df,
) = createSpatialData()


def createDarkTheme():
    back_colors = {"superdark-blue": "rgb(31,38,42)"}
    # create our custom_dark theme from the plotly_dark template
    plt_io.templates["custom_dark"] = plt_io.templates["plotly_dark"]

    # set the paper_bgcolor and the plot_bgcolor to a new color
    # plt_io.templates["custom_dark"]["layout"]["paper_bgcolor"] = "#30404D"
    # plt_io.templates["custom_dark"]["layout"]["plot_bgcolor"] = "#30404D"

    plt_io.templates["custom_dark"]["layout"]["paper_bgcolor"] = back_colors[
        "superdark-blue"
    ]
    plt_io.templates["custom_dark"]["layout"]["plot_bgcolor"] = back_colors[
        "superdark-blue"
    ]

    # you may also want to change gridline colors if you are modifying background
    plt_io.templates["custom_dark"]["layout"]["yaxis"]["gridcolor"] = "#4f687d"
    plt_io.templates["custom_dark"]["layout"]["xaxis"]["gridcolor"] = "#4f687d"
    return


###############################################################################################################################
# Create a theme
###############################################################################################################################
createDarkTheme()


def createRentalMap(df, fixed_radius, nbd_or_grp):
    """
    This function takes in a dataframe and applies a fucntion that creates circle markers for every 
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
        # tiles="Stamen Toner",
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
            # radius=15,
            weight=3,
            # color=point_row["glow_marker_color"],
            # fill_color=point_row["glow_marker_color"],
            color=dashboard_colors["medium-blue-grey"],
            fill_color=dashboard_colors["medium-blue-grey"],
            fill_opacity=0.5,
        ).add_child(folium.Tooltip(f"{point_row.name}: {text}",)).add_to(this_map)

        # Add text of count within circle
        folium.map.Marker(
            [point_row["latitude"], point_row["longitude"]],
            icon=DivIcon(
                icon_size=(150, 36),
                icon_anchor=(0, 0),
                html='<div style="font-size: 12pt; font-weight:bold;color=red">%s</div>'
                % text,
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

        text = f'Neighborhood: {point_row["neighbourhood_cleansed"]}<br>Is available: {is_available}<br>Accommodates: {point_row["accommodates"]}<br>Rent (In USD): {point_row["price"]}'
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

    # Make a choropleth
    # Use the provided geojson file
    nbd_geo_file = r"data/neighbourhoods.geojson"
    filtered_df = filtered_df.rename(
        columns={"neighbourhood_cleansed": "neighbourhood_cleansed_count"}
    )
    filtered_df = filtered_df.reset_index()

    # Colors allowed : https://github.com/dsc/colorbrewer-python
    this_map.choropleth(
        geo_data=nbd_geo_file,
        data=filtered_df,
        columns=["neighbourhood_cleansed", "neighbourhood_cleansed_count"],
        key_on="feature.properties.neighbourhood",
        fill_color="Greys",
        fill_opacity=0.3,
        line_opacity=0.6,
        legend_name="Listing Count",
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


def createSankeyChart(nbd):
    """This function creates a figure (chart) that is a Sankey Chart for the neighborhood that is input

    Args:
        nbd ([type]): [Neighborhood Group]
    Returns a Sankey figure object    
    """
    nbd_col = (
        "neighbourhood_group_cleansed" if nbd == "All" else "neighbourhood_cleansed"
    )

    if nbd != "All":
        three_proptype_df = rental_df[
            rental_df["neighbourhood_group_cleansed"] == nbd
        ].copy()
    else:
        three_proptype_df = rental_df.copy()

    three_proptype_df = three_proptype_df[[nbd_col, "property_type_class"]].copy()

    # Limit types of property to House, Private Room and Shared Room
    three_proptype_df = three_proptype_df[
        three_proptype_df["property_type_class"].str.contains(
            "House|Private Room|Shared Room|Condominium|Seviced apartment|Apartment|Townhouse"
        )
    ]

    # we are not interested in Houseboats in the Sankey chart
    three_proptype_df = three_proptype_df[
        ~three_proptype_df["property_type_class"].str.contains("Houseboat")
    ]
    label_list = three_proptype_df[nbd_col].unique().tolist()
    label_list.sort()
    label_list += three_proptype_df["property_type_class"].unique().tolist()

    # Create a new column count_listings with number of listings per neighborhood/neighborhood group and propert type
    sankey_df = three_proptype_df.groupby([nbd_col, "property_type_class"]).agg(
        count_listings=("property_type_class", "count")
    )
    sankey_df = sankey_df.reset_index()

    # Create an dictionary of the indices of the nodes we are going to link (the sankey cchart links are created between these indices)
    label_idx_dict = {}
    for idx, label in enumerate(label_list):
        label_idx_dict[label] = idx

    # Use the dictionary to map the nodes to the indizes in the dataframe
    sankey_df["nbd_idx"] = sankey_df[nbd_col].map(label_idx_dict)
    sankey_df["prop_idx"] = sankey_df["property_type_class"].map(label_idx_dict)

    color_list = full_color_list[: len(three_proptype_df[nbd_col].unique().tolist())]
    group_color = dict(zip(list(sankey_df.groupby(nbd_col).groups.keys()), color_list,))
    sankey_df["color_link"] = sankey_df[nbd_col].map(group_color)

    source = sankey_df["nbd_idx"].tolist()
    target = sankey_df["prop_idx"].tolist()
    values = sankey_df["count_listings"].tolist()
    # There are as many colors as nodes = 17 + 3
    if nbd == "All":
        color_node = full_color_list + ["#befdb7", "#1B03A3", "#FEFCD7"]
    else:
        color_node = full_color_list[: len(label_list)]

    # For every neighborhood we use the same color for the link
    color_link = sankey_df["color_link"].tolist()

    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=label_list,
                    color=color_node,
                    customdata=label_list,
                    hovertemplate="%{customdata} has  %{value} listings<extra></extra>",
                ),
                link=dict(
                    source=source,
                    target=target,
                    value=values,
                    color=color_link,
                    hovertemplate="Link from  %{source.customdata}<br />"
                    + "to %{target.customdata}<br />has  %{value} listings<extra></extra>",
                ),
            )
        ]
    )

    fig.update_layout(
        title_text="Available houses and rooms",
        font_size=12,
        title_font_color=dashboard_colors["medium-blue-grey"],
        font=dict(size=12, color=dashboard_colors["medium-blue-grey"]),
    )
    # Set the theme
    fig.layout.template = "custom_dark"

    return fig


def createAreaPropTypeMap(nbd):
    """This function returns a horizontal bar chart

        Args:
        nbd ([type]): [Neighborhood Group]
        Returns a horizontal bar graph figure object    
    """

    if nbd == "All":
        prop_count_df = rental_df.copy()
    else:
        prop_count_df = rental_df[
            rental_df["neighbourhood_group_cleansed"] == nbd
        ].copy()

    nbd_col = (
        "neighbourhood_group_cleansed" if nbd == "All" else "neighbourhood_cleansed"
    )

    prop_count_df = prop_count_df.groupby([nbd_col, "property_type_class"]).agg(
        count_list=("property_type_class", "count")
    )
    prop_count_df = prop_count_df.reset_index()
    prop_count_df = prop_count_df.sort_values("property_type_class", ascending=True)

    fig = px.bar(
        prop_count_df,
        y=prop_count_df.property_type_class,
        x=prop_count_df.count_list,
        color=prop_count_df[nbd_col],
        title="Rentable property type counts",
        labels={
            nbd_col: "Neighborhood",
            "property_type_class": "Property Type",
            "count_list": "Number of listings",
        },
        color_discrete_sequence=px.colors.qualitative.Pastel,
        orientation="h",
    )

    fig.update_layout(
        title_text="Rentable property type counts",
        font_size=12,
        title_font_color=dashboard_colors["medium-blue-grey"],
    )
    # Set the theme
    fig.layout.template = "custom_dark"

    return fig
