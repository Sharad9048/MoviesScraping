import requests
from bs4 import BeautifulSoup
from functools import reduce
import pandas as pd
import logging, os

logging.basicConfig(
    level = logging.ERROR,
    format = "%(asctime)s %(levelname)s %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
    filename= "scraping.log"
)

processId = os.getpid()

# This URL will used for navigating to between pages and individual movie details
baseUrl = 'https://www.themoviedb.org'

# This will help us from being caught by the BOT on the above website
header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'}

# Making the List of 50 page URL
urls = [baseUrl+f'/movie?page={pageNo}' for pageNo in range(1,51)]

def tryRequestingData(url):
    """
    @input:str - Accepts only URL
    @output:str - Returns a HTML string

    The function will keep requesting data from the website URL until the retries are over
    """
    
    try:
        # Getting HTML data from the url
        sourceData = requests.get(url, headers=header)
    
        # Declaring Maximum retries
        retryCount = 10

        # Checking the status code and re-atempting to get the HTML data
        while sourceData.status_code != 200:
            
            # Checking if number of retries has finished
            if retryCount <=0:
                logging.error("Failed to get Response 200 from URL: {url}")
                logging.info("Safely terminating...")
                exit()          # The program will be terminated
            else:
                retry-=1        # Decrementing number of Retries
        
        # Re-attempting to get the HTML data
        sourceData = requests.get(url, headers=header)

    except:
        logging.error(f"Invalid URL: {url}")
        logging.info("Safely terminating...")
        exit()

    return sourceData.text

def getMovieDetail(movieSoupData):
    """
    @Input:BeautifulSoup - The function will accept BeautifulSoup Object
    @Output:dict - The function will return a dictionary data
        
        Example: 
            >> soupObject = BeautifulSoup(htmlData, 'lxml')
            >> data = getMovieDetail(soupObject)
            >> print(data)
            {
                "Title" : "Movie",
                "Date" : "Dec 06, 2023",
                "Rating" : "72",
                "Genres" : "Comedy,Family,Fantasy",
                "Runtime" : "1h 57m",
                "Overview" : "Movie Description",
                "Director" : "Movie Director",
            }

    The will extract the following data from the movie block and movie detail page
    * Title
    * Data
    * Rating
    * Genres
    * Runtime
    * Overview
    * Director of the movie
    """

    # Extracting title from the h2 tag
    movieTitle = movieSoupData.find('h2').text

    # Extracting date of the movie from p tag
    movieDate = movieSoupData.find('p').text

    # Extracting the path for navigating to the movie detail page
    moviePath = movieSoupData.find('h2').find('a').get('href')

    # Extracting the movie detail HTML page using the path stored above
    movieSourceData = tryRequestingData(baseUrl + moviePath)

    # Converting HTML string to BeautifulSoup object
    movieDetailPage = BeautifulSoup(movieSourceData, 'lxml')
    
    try:
        try:
            # 1st Extraction rating perventage of the movie from span element inside div element of class 'percent'
            firstRatingExt = movieDetailPage.find('div', class_ = 'percent').find('span')

            # 2nd Extraction of list of string from the class inside the span element
            secondRatingExt = firstRatingExt.get('class')

            # Finally extracting rating from 2nd element of the list which is a string and removing the alphabetical characters
            rating = secondRatingExt[1].replace('icon-r','')

            # Checking and changing the rating to "NA" if rating is no available
            if rating == "NR":
                rating = 'NA'
        except AttributeError:
            logging.error(f'{processId}|rating|data not found|NA|{movieTitle}|{baseUrl + moviePath}')
            rating = 'NA'
    except:
        logging.error(f'{processId}|rating|operation failed|NA|{movieTitle}|{baseUrl + moviePath}')
        rating = 'NA'

    try:
        try:
            # Extracting list of genres of the movie inside span element of class 'genres'
            genresList = [genre.text for genre in movieDetailPage.find('span', class_ = 'genres').find_all('a')]
            
            # Joining all the genre string with comma seperated string
            genres =','.join(genresList)
        except AttributeError:
            logging.error(f'{processId}|genres|data not found|NA|{movieTitle}|{baseUrl + moviePath}')
            genres = 'NA'
    except:
        logging.error(f'{processId}|genres|operation failed|NA|{movieTitle}|{baseUrl + moviePath}')
        genres = 'NA'
    
    try:
        # Using exception handling for the movies that don't have runtime data
        try:
            # Extraction Runtime data of the movie inside span elemnet of class 'runtime'
            runtime = movieDetailPage.find('span', class_ = 'runtime').text.replace('\n','').strip()
        except AttributeError:
            logging.error(f'{processId}|runtime|data not found|NA|{movieTitle}|{baseUrl + moviePath}')
            runtime = 'NA'
    except:
        logging.error(f'{processId}|runtime|operation failed|NA|{movieTitle}|{baseUrl + moviePath}')
        runtime = 'NA'
    
    try:
        try:
            # Extraction overview of the movie inside p tag
            overview = movieDetailPage.find('p').text
        except AttributeError:
            logging.error(f'{processId}|overview|data not found|NA|{movieTitle}|{baseUrl + moviePath}')
            overview = 'NA'
    except:
        logging.error(f'{processId}|overview|operation failed|NA|{movieTitle}|{baseUrl + moviePath}')
        overview = 'NA'


    try:
        try:
            # Running a loop to scan 'Director' string inside a group li tag of class 'profile'
            for profile in movieDetailPage.find_all('li', class_ = 'profile'):

                # Checking if the 'Director' string is present in the current li tag
                if 'Director' in profile.text:

                    # Extracting the director of the movie inside the a tag of the current li tag
                    director = profile.find('a').text

                    # Ending the loop since the director detail was found
                    break
        except AttributeError:
            logging.error(f'{processId}|director|data not found|NA|{movieTitle}|{baseUrl + moviePath}')
            director = 'NA'
    except:
        logging.error(f'{processId}|director|operation failed|NA|{movieTitle}|{baseUrl + moviePath}')
        director = 'NA'

    # Compiling all the collected movie detail into a dictionary
    movieData = {
        "Title" : movieTitle,
        "Date" : movieDate,
        "Rating" : rating,
        "Genres" : genres,
        "Runtime" : runtime,
        "Overview" : overview,
        "Director" : director,
    }

    return movieData

def getAllMoviesDetail(url):
    """
    @input:str - Accepts only URL
    @output:list - Return a List of movie data Dictionary inside a List
    """
    # Getting HTML data from the url
    sourceData = tryRequestingData(url)
    
    # Converting the HTML string data to soup data
    popularMoviesPage = BeautifulSoup(sourceData, 'lxml')

    # Extracting the list of movie blocks which are div element of class 'card style_1'
    movieBlockList = popularMoviesPage.find_all('div',class_='card style_1')

    # Using map function to get movie data by passing the function getMovieDetail and list of movieBlock bs4 objects
    movieDetailList = list(map(getMovieDetail, movieBlockList))

    return movieDetailList

# Extracting movie detail using the list of urls of 50 pages
pagesMovieDetailList = map(getAllMoviesDetail, urls)

# Reducing collection of list of movie details to list of movie detail
movieDetailList = reduce(lambda list1, list2: list1 + list2, pagesMovieDetailList)

# Converting the compressed data into a tuple
allMoviesData = tuple(movieDetailList)

# Creating a pandas dataframe from the tuple of movie detail
moviesDf = pd.DataFrame(allMoviesData)

# Saving the dataframe in an excel file
moviesDf.to_excel('Movies.xlsx')
