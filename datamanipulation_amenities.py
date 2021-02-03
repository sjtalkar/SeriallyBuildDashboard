import pandas as pd
import numpy as np

import folium
from folium.features import DivIcon

from sklearn import preprocessing

# For word cloud and amenities bar chart
from nltk.tokenize import regexp_tokenize
from nltk import FreqDist


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


def createPropertyTypeCol(rental_df):
    """This function adds a column called property_type_class to the dataframe 
    Args:
        rental_df ([type]): [The dataframe has a column called property_type]

    Returns:
        [type]: [Dataframe with a more concise list of property types]
    """

    # Property types Private room and Shared Room identified
    property_df = rental_df[["property_type"]].copy()
    property_df.loc[
        property_df["property_type"].str.contains("Private room|Room in"),
        "property_type",
    ] = "Private Room"
    property_df.loc[
        property_df["property_type"].str.contains("Shared room"), "property_type"
    ] = "Shared Room"

    # Extrac the second half of all "Entire" property types to get the actual type such as house..
    property_df.loc[
        property_df["property_type"].str.contains("Entire "), "property_type"
    ] = (
        property_df.loc[
            property_df["property_type"].str.contains("Entire "), "property_type"
        ]
        .str.replace("Entire ", "")
        .str.capitalize()
    )

    rental_df["property_type_class"] = property_df["property_type"]

    return rental_df


##############################################################################################################
# Clean up the dataframe
##############################################################################################################
def cleanRentalDF(filename):

    # Read the data into a dataframe
    full_df = pd.read_csv(filename)
    # select out the columns we are interested in
    rental_df = full_df[
        [
            "id",
            "price",
            "listing_url",
            "host_id",
            "host_response_rate",
            "host_response_time",
            "host_acceptance_rate",
            "review_scores_communication",
            "review_scores_location",
            "review_scores_value",
            "review_scores_checkin",
            "reviews_per_month",
            "review_scores_cleanliness",
            "license",
            "instant_bookable",
            "number_of_reviews",
            "first_review",
            "last_review",
            "neighbourhood_cleansed",
            "neighbourhood_group_cleansed",
            "latitude",
            "longitude",
            "accommodates",
            "bathrooms_text",
            "property_type",
            "has_availability",
            "availability_30",
            "availability_60",
            "availability_90",
            "availability_365",
        ]
    ].copy()

    # Make price a float column
    rental_df["price"] = (
        rental_df["price"].str.replace("$", "").str.replace(",", "").astype("float64")
    )

    # Change host response rate from string to float so that it is a continuous value
    # TBD Look for average for the host - should I look for nans in hosts that have multiple records and set Nan to 0 oly for hosts that have only one record?
    # Mean of their reponse rate for the rest?
    # How about impute?

    # Convert the response rate to float
    rental_df["host_response_rate_percent"] = (
        rental_df["host_response_rate"].str.replace("%", "").astype("float64")
    )
    rental_df["host_response_rate_percent"] = rental_df.groupby(["host_id"])[
        "host_response_rate_percent"
    ].transform(lambda x: x.fillna(x.mean()))
    # All the values that are still Nan, we do not have any info about and so fill with zero
    rental_df["host_response_rate_percent"] = rental_df[
        "host_response_rate_percent"
    ].fillna(0)
    rental_df = rental_df.drop("host_response_rate", axis="columns")

    # Change response time to one within a dict
    # Question should we set Nans to -0 or to a very high number ( highest rank is least reponsive)
    rank_response_time = {
        "within an hour": 1,
        "within a few hours": 2,
        "within a day": 3,
        "a few days or more": 4,
    }
    rental_df["host_reponse_time_rank"] = rental_df["host_response_time"].map(
        rank_response_time
    )
    rental_df["host_reponse_time_rank"] = rental_df["host_reponse_time_rank"].fillna(0)
    rental_df = rental_df.drop("host_response_time", axis="columns")

    # Use the same logic as host_reponse_rate for host_acceptance_rate
    rental_df["host_acceptance_rate_percent"] = (
        rental_df["host_acceptance_rate"].str.replace("%", "").astype("float64")
    )
    rental_df["host_acceptance_rate_percent"] = rental_df.groupby(["host_id"])[
        "host_acceptance_rate_percent"
    ].transform(lambda x: x.fillna(x.mean()))
    # All the values that are still Nan, we do not have any info about and so fill with zero
    rental_df["host_acceptance_rate_percent"] = rental_df[
        "host_acceptance_rate_percent"
    ].fillna(0)
    rental_df = rental_df.drop("host_acceptance_rate", axis="columns")

    # (‘t’ means available and ‘f’ means not available)
    # *Convert t (*true) = 1 , f (false) = 0

    availability_code_dict = {
        "t": 1,
        "f": 0,
    }

    rental_df["instant_bookable"] = rental_df["instant_bookable"].map(
        availability_code_dict
    )
    rental_df["has_availability"] = rental_df["has_availability"].map(
        availability_code_dict
    )

    # Question what must be done for dates not present?
    rental_df["first_review"] = pd.to_datetime(rental_df["first_review"])
    rental_df["last_review"] = pd.to_datetime(rental_df["last_review"])

    # Add a column for a smaller list of property types
    rental_df = createPropertyTypeCol(rental_df)

    return rental_df


################################################################################################################
# Call the cleanup function and setup a global dataframe
################################################################################################################
full_df = cleanRentalDF("data\listings_1.csv")

################################################################################################################
# Create data for maps
################################################################################################################

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

    return full_df, rental_geo_df, rental_neighborhood_df, rental_grp_nbd_df


def get_nbdgroups():
    """
    This function returns a dictionary of Neighborhood groups to populate a selection filter
    Input: None
    Returns: Dictionary
    """
    nbd_groups = list(full_df.neighbourhood_group_cleansed.unique())
    nbd_groups.sort()
    return ["All"] + nbd_groups


#############################################################################################################################################
##################Create a new dataframe for amenities
#############################################################################################################################################


def getAmenitiesTokens(cell_val):
    return regexp_tokenize(cell_val, "([\w\s\d']+), ")


def createAmentiesDF(filename):
    amenities_df = pd.read_csv(filename)
    amenities_df["amenities"] = amenities_df["amenities"].replace(
        {
            "\[": "",
            "\]": "",
            '"': "",
            r"\\u2019": r"'",
            r"\\u2013": "-",
            r"\\u00a0": "",
        },
        regex=True,
    )
    amenities_df["amenities"] = amenities_df["amenities"].str.lower()
    amenities_df["amenities_tokens"] = amenities_df["amenities"].apply(
        getAmenitiesTokens
    )
    return amenities_df


def createTokenDistDF(topn, tokenDist):
    tokenDist_df = pd.DataFrame.from_dict(tokenDist, orient="index")
    tokenDist_df = tokenDist_df.reset_index()
    tokenDist_df.columns = ["amenity_token", "freq"]

    # Clean brand names and specifics from  some specifuc amenities
    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("refrigerator"), "amenity_token"
    ] = "refrigerator"
    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("mini fridge"), "amenity_token"
    ] = "mini fridge"

    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("electric stove"), "amenity_token"
    ] = "electric stove"
    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("induction stove"), "amenity_token"
    ] = "induction stove"
    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("gas stove"), "amenity_token"
    ] = "gas stove"
    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("stove"), "amenity_token"
    ] = "stove"

    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("tv"), "amenity_token"
    ] = "tv"

    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("electric oven"), "amenity_token"
    ] = "electric oven"
    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("gas oven"), "amenity_token"
    ] = "gas oven"
    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("induction oven"), "amenity_token"
    ] = "induction oven"
    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("oven"), "amenity_token"
    ] = "oven"

    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("shampoo"), "amenity_token"
    ] = "shampoo"
    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("conditioner"), "amenity_token"
    ] = "conditioner"
    tokenDist_df.loc[
        (tokenDist_df["amenity_token"].str.contains("body soap"))
        | (tokenDist_df["amenity_token"].str.contains("body wash")),
        "amenity_token",
    ] = "body soap"
    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("soap"), "amenity_token"
    ] = "soap"

    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("paid parking"), "amenity_token"
    ] = "paid parking"
    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("free parking"), "amenity_token"
    ] = "free parking"

    tokenDist_df.loc[
        (tokenDist_df["amenity_token"].str.contains("paid"))
        & (
            (tokenDist_df["amenity_token"].str.contains("parking"))
            | (tokenDist_df["amenity_token"].str.contains("carport"))
        ),
        "amenity_token",
    ] = "paid parking"
    tokenDist_df.loc[
        (tokenDist_df["amenity_token"].str.contains("free"))
        & (
            (tokenDist_df["amenity_token"].str.contains("parking"))
            | (tokenDist_df["amenity_token"].str.contains("carport"))
        ),
        "amenity_token",
    ] = "free parking"

    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("sound system"), "amenity_token"
    ] = "sound system"
    tokenDist_df.loc[
        tokenDist_df["amenity_token"].str.contains("hot tub"), "amenity_token"
    ] = "hot tub"

    #################################################################
    # combine the change amenities together
    tokenDist_df = tokenDist_df.groupby(["amenity_token"]).agg(freq=("freq", "sum"))
    tokenDist_df = tokenDist_df.sort_values(by="freq", ascending=False)

    #################################################################
    # create slider for this number of top Limit slider to 10 min and 50 max
    top_tokenDist_df = tokenDist_df.iloc[:topn].copy().reset_index()
    top_tokenDist_df["amenity_token"] = top_tokenDist_df["amenity_token"].apply(
        lambda x: x.capitalize()
    )

    return top_tokenDist_df


amenities_df = createAmentiesDF(r"data/listings_onlyamenities.csv")

