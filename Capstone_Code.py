## Code Setup Block

#Import / Load / ETC.
import requests 
import pandas as pd 
import numpy as np 
import random 
import matplotlib.pyplot as plt
from IPython.display import Image 
from IPython.core.display import HTML 
# tranforming json file into a pandas dataframe library
from pandas.io.json import json_normalize
import folium 

#Constants
CLIENT_ID = '45AFC25M5DD2S53HBPUYESDMWIYXYDWBIPX0I0QRWTFRDXGY' # your Foursquare ID
CLIENT_SECRET = 'VJ5M5OCUSYPJ1WFYEIC11VCZQ44MOKUXFXQQBDW4WSXCL3QR' # your Foursquare Secret
VERSION = '20180604'
print('Your credentails:')
print('CLIENT_ID: ' + CLIENT_ID)
print('CLIENT_SECRET:' + CLIENT_SECRET)

#Functions

# Extracts the category of the venue
def get_category_type(row):
    try:
        categories_list = row['categories']
    except:
        categories_list = row['venue.categories']
        
    if len(categories_list) == 0:
        return None
    else:
        return categories_list[0]['name']

# Assigns venues to one point or another for purpose comparing where in city to mark as point for development & Updates points for iteration
def assign_members(x, y, centers):
    colors_map = np.array(['b', 'r'])
    compare_to_first_center = np.sqrt(np.square(np.array(x) - centers[0][0]) + np.square(np.array(y) - centers[0][1]))
    compare_to_second_center = np.sqrt(np.square(np.array(x) - centers[1][0]) + np.square(np.array(y) - centers[1][1]))
    class_of_points = compare_to_first_center > compare_to_second_center
    colors = colors_map[class_of_points + 1 - 1]
    return colors, class_of_points
def update_centers(x1, x2, class_of_points):
    center1 = [np.mean(np.array(x)[~class_of_points]), np.mean(np.array(y)[~class_of_points])]
    center2 = [np.mean(np.array(x)[class_of_points]), np.mean(np.array(y)[class_of_points])]
    return [center1, center2]

# Plots points and venues 
def plot_points(centroids=None, colors='g', figure_title=None):
    # plot the figure
    fig = plt.figure(figsize=(15, 10))  # create a figure object
    ax = fig.add_subplot(1, 1, 1)
    centroid_colors = ['bx', 'rx']
    if centroids:
        for (i, centroid) in enumerate(centroids):
            ax.plot(centroid[0], centroid[1], centroid_colors[i], markeredgewidth=5, markersize=20)
    plt.scatter(x, y, s=500, c=colors)
    # add labels to axes
    ax.set_xlabel('lng', fontsize=20)
    ax.set_ylabel('lat', fontsize=20)
    # add title to figure
    ax.set_title(figure_title, fontsize=24)
    plt.show()
    return null


## Set Variables Block

# City List
location = {'City':['Birmingham_AL', 'Atlanta_GA', 'Alexandria_VA', 'Denver_CO', 'Seattle_WA'],
            'Latitude':[33.5010844, 33.754735, 38.8052192, 39.7491072, 47.6017105],
            'Longitude':[-86.797018, -84.3903139, -77.0486295, -104.9955414, -122.331915]}
location = pd.DataFrame(data = location)

# User Variable Set
radius = 4000 # m radius (recommend 4000 to give ~2km radius from center and minimum 1km from furthest test points at 0.01 degree variation in testing)
LIMIT = 100 #venues in a list
latlon_var = 0.01 #how many degrees lat and long to vary to determine if point further from center of city is better (each degree is ~110km; 0.01deg = ~1km)
numIter = 4 #Number of times to iterate centers to determine best place to score from

#Preparing variables for main code
numCity = range(len(location.City))
results = []
center_results = []
venues = []
center_venues = []
nearby_venues=[]
score = []
fResults = []

# User Confidence in Variable Setting Checks
print(location.head())


## Main Code Block

# Call 4Square API

for z in numCity: #For each city in list, "explore" location for venues
    url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
        CLIENT_ID, 
        CLIENT_SECRET, 
        VERSION, 
        location.Latitude[z], 
        location.Longitude[z], 
        radius, 
        LIMIT) #URL for 4Square API
    results.append(requests.get(url).json()) #Appends results of API call to "results" arrary set up previously 
    venues.append(results[z]['response']['groups'][0]['items']) #Pulls out data we want from results    

# Organize and Score Data

for z in numCity: #For each city in explored, find relevent data, pick point of development, and score it
    nearby_venues = json_normalize(venues[z])
    # filter columns
    filtered_columns = ['venue.name', 'venue.categories', 'venue.location.lat', 'venue.location.lng']
    nearby_venues =nearby_venues.loc[:, filtered_columns]
    # filter the category for each row
    nearby_venues['venue.categories'] = nearby_venues.apply(get_category_type, axis=1)
    # clean columns
    nearby_venues.columns = [col.split(".")[-1] for col in nearby_venues.columns]
    x = nearby_venues.lng
    y = nearby_venues.lat
    # Checking points in each cardinal direction to determine if shifting point of development 
    centers = [[location.Longitude[z], location.Latitude[z]+latlon_var], [location.Longitude[z], location.Latitude[z]-latlon_var]]
    # Iterate to move points to cover most venues
    for i in range(numIter):
        colors, class_of_points = assign_members(x, y, centers)
        centers = update_centers(x, y, class_of_points)
    #plot_points(centers, colors, figure_title='Centers of Venues')
    splitNS = assign_members(x, y, centers) #Determines how many venues are in each center's area of influence
    #split = '{} South Center Venues: {} / North Center Venues: {}'.format(location.City[z], np.count_nonzero(splitNS[1]), len(splitNS[0])-np.count_nonzero(splitNS[1])) #Sanity Check
    #print(split)
    # Use point previously determined to be better to start this set of iterations for East and West
    if len(splitNS[0])-np.count_nonzero(splitNS[1]) > np.count_nonzero(splitNS[1]):
        centers = [[location.Longitude[z]+latlon_var,centers[1][1]],[location.Longitude[z]-latlon_var,centers[1][1]]]
    elif len(splitNS[0])-np.count_nonzero(splitNS[1]) < np.count_nonzero(splitNS[1]):
        centers = [[location.Longitude[z]+latlon_var,centers[0][1]],[location.Longitude[z]-latlon_var,centers[0][1]]]
    #Iterate, again, to move points to cover most venues using new center locations to start
    for i in range(numIter):
        colors, class_of_points = assign_members(x, y, centers)
        centers = update_centers(x, y, class_of_points)
    splitEW = assign_members(x, y, centers) #Determines how many venues are in each center's area of influence
    #split = '{} East Center Venues: {} / West Center Venues: {}'.format(location.City[z], np.count_nonzero(splitEW[1]), len(splitEW[0])-np.count_nonzero(splitEW[1])) #Sanity Check
    #print(split)
    # Use point previously determined to be better to start this set of iterations for East and West
    if len(splitEW[0])-np.count_nonzero(splitEW[1]) > np.count_nonzero(splitEW[1]):
        center = [centers[1][0],centers[1][1]]
    elif len(splitEW[0])-np.count_nonzero(splitEW[1]) < np.count_nonzero(splitEW[1]):
        center = [centers[0][0],centers[0][1]]
    url = 'https://api.foursquare.com/v2/venues/explore?&client_id={}&client_secret={}&v={}&ll={},{}&radius={}&limit={}'.format(
        CLIENT_ID, 
        CLIENT_SECRET, 
        VERSION, 
        center[0], 
        center[1], 
        1000,#m radius, 
        500) #limit of venue results #URL for 4Square API to get all venues within 1km of venue
    center_results.append(requests.get(url).json())
    center_venues.append(results[z]['response']['groups'][0]['items'])
    venue_id = []
    scoredf = pd.DataFrame({'Category':[], 'Rating':[]})
    for y in range(len(center_venues)):
        venue_id.append(center_venues[z][y]['venue']['id'])
    url = 'https://api.foursquare.com/v2/venues/{}?client_id={}&client_secret={}&v={}'.format(venue_id[0], CLIENT_ID, CLIENT_SECRET, VERSION)
    result = requests.get(url).json()
    for y in range(len(venue_id)):
        url = 'https://api.foursquare.com/v2/venues/{}?client_id={}&client_secret={}&v={}'.format(venue_id[y], CLIENT_ID, CLIENT_SECRET, VERSION)
        result = requests.get(url).json()
        scoredf['Category'][y] = (result['response']['venue']['categories'][0]['shortName'])
        scoredf['Rating'][y] = (result['response']['venue']['rating'])
    catUnique = len(scoredf['Category'].unique())/50
    ratMean = scoredf.Rating.mean()
    score.append(ratMean+catUnique)

# Print Final Result
for z in range(len(location.City)):
    fResults.append([location.City[z],score[z]])
fResults = pd.DataFrame(data = fResults)
fResults.columns = ['Location', 'Score']
fResults.set_index('Location', inplace = True)
fCity = fResults['Score'].idxmax()
fStatement = 'The best city for development is {} with a score of {}\n The mean score for tested locations was {}\n Full Results are below: \n'.format(fCity, fResults['Score'].max(), fResults['Score'].mean())
print(fStatement)
print(fResults)