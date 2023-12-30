import requests
from bs4 import BeautifulSoup

import logging, os

# Configuring Loggging program
logging.basicConfig(
    level = logging.INFO,       # It will store logs whose severity greater than INFO
    format = "%(asctime)s %(levelname)s %(message)s",       # It is the format in which the logging will b
    datefmt = "%Y-%m-%d %H:%M:%S",      # Date format for logger
    filename= "scraping.log"        # File in which the logs must be stored
)

# Process ID will be used for storing logs
processId = os.getpid()

# This URL will used for navigating to between pages and individual movie details
baseUrl = 'https://www.themoviedb.org'

# This will help us from being caught by the BOT on the above website
header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'}

def tryRequestingData(url):
    """
    @input:str - Accepts only URL
    @output:str - Returns a HTML string

    The function will keep requesting data from the website URL until the retries are over
    """
    
    # Declaring Maximum retries
    retryCount = 10

    # Checking the status code and re-atempting to get the HTML data
    while retryCount >= 0:
        try:
            # Getting HTML data from the url
            sourceData = requests.get(url, headers=header)

            # Checking if number of retries has finished
            if sourceData.status_code == 200:
                return sourceData.text      # Decrementing number of Retries
            else:
                logging.info(f"{processId}|Status Code is {sourceData.status_code}|Retrying...")
        
        except:
            if retryCount==0:
                # If retry count is 0 the URL will be invalid, it will be recorded as an error in the log and raise an exception
                logging.error(f"Invalid URL: {url}")
                raise RuntimeError("Invalid URL")
            else:
                # It will record retrying info in logs until retries are exhausted
                logging.info(f"{processId}|Retrying...|{url}")
        finally:
            retryCount-=1


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
                "Overview" : "The MC is very strong",
                "Director" : "Jake",
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
    try:
        # Extracting the movie detail HTML page using the path stored above
        movieSourceData = tryRequestingData(baseUrl + moviePath)
    except RuntimeError:
        # If requesting movie HTML data fails then:
        # the missing values info will be stored in log file
        logging.info(f'{processId}|rating,genres,runtime,overview,director|movie detail page not found|NA|{movieTitle}|{baseUrl + moviePath}')
        # the remaining fields will have default value as 'NA'
        movieData = {
            "Title" : movieTitle,
            "Date" : movieDate,
            "Rating" : "NA",
            "Genres" : "NA",
            "Runtime" : "NA",
            "Overview" : "NA",
            "Director" : "NA",
        }
        # returning an incomplete movie data dictionary
        return movieData

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
            # If the element of rating is missing, the info of the missing data will be recorded in the log file
            logging.info(f'{processId}|rating|element not found|NA|{movieTitle}|{baseUrl + moviePath}')
            # the rating will store 'NA'
            rating = 'NA'
    except:
        # Any other exception will be recorded as an error
        logging.error(f'{processId}|rating|operation failed|NA|{movieTitle}|{baseUrl + moviePath}')
        # the rating will store 'NA'
        rating = 'NA'

    try:
        try:
            # Extracting list of genres of the movie inside span element of class 'genres'
            genresList = [genre.text for genre in movieDetailPage.find('span', class_ = 'genres').find_all('a')]
            
            # Joining all the genre string with comma seperated string
            genres =','.join(genresList)
        except AttributeError:
            # If the element of genres is missing, the info of the missing data will be recorded in the log file
            logging.info(f'{processId}|genres|element not found|NA|{movieTitle}|{baseUrl + moviePath}')
            # the genres will store 'NA'
            genres = 'NA'
    except:
        # Any other exception will be recorded as an error
        logging.error(f'{processId}|genres|operation failed|NA|{movieTitle}|{baseUrl + moviePath}')
        # the genres will store 'NA'
        genres = 'NA'
    
    try:
        # Using exception handling for the movies that don't have runtime data
        try:
            # Extraction Runtime data of the movie inside span elemnet of class 'runtime'
            runtime = movieDetailPage.find('span', class_ = 'runtime').text.replace('\n','').strip()
        except AttributeError:
            # If the element of runtime is missing, the info of the missing data will be recorded in the log file
            logging.info(f'{processId}|runtime|element not found|NA|{movieTitle}|{baseUrl + moviePath}')
            # the runtime will store 'NA'
            runtime = 'NA'
    except:
        # Any other exception will be recorded as an error
        logging.error(f'{processId}|runtime|operation failed|NA|{movieTitle}|{baseUrl + moviePath}')
        # the runtime will store 'NA'
        runtime = 'NA'
    
    try:
        try:
            # Extraction overview of the movie inside p tag
            overview = movieDetailPage.find('p').text
        except AttributeError:
            # If the element of overview is missing, the info of the missing data will be recorded in the log file
            logging.info(f'{processId}|overview|element not found|NA|{movieTitle}|{baseUrl + moviePath}')
            # the overview will store 'NA'
            overview = 'NA'
    except:
        # Any other exception will be recorded as an error
        logging.error(f'{processId}|overview|operation failed|NA|{movieTitle}|{baseUrl + moviePath}')
        # the overview will store 'NA'
        overview = 'NA'

    director = "NA"
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
            # If the element of director is missing, the info of the missing data will be recorded in the log file
            logging.info(f'{processId}|director|data not found|NA|{movieTitle}|{baseUrl + moviePath}')
            # the director will store 'NA'
            director = 'NA'
    except:
        # Any other exception will be recorded as an error
        logging.error(f'{processId}|director|operation failed|NA|{movieTitle}|{baseUrl + moviePath}')
        # the director will store 'NA'
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

    It will Extract all the movie data from URL HTML page
    """
    try:
        # Getting HTML data from the url
        sourceData = tryRequestingData(url)
    except RuntimeError:
        # If requesting HTML data fails the function will return an empty list
        return []
    
    # Converting the HTML string data to soup data
    popularMoviesPage = BeautifulSoup(sourceData, 'lxml')

    # Extracting the list of movie blocks which are div element of class 'card style_1'
    movieBlockList = popularMoviesPage.find_all('div',class_='card style_1')

    # Using map function to get movie data by passing the function getMovieDetail and list of movieBlock bs4 objects
    movieDetailList = tuple(map(getMovieDetail, movieBlockList))

    return movieDetailList


if __name__=="__main__":

    import pandas as pd
    from functools import reduce

    # Making the List of 50 page URL
    urls = [baseUrl+f'/movie?page={pageNo}' for pageNo in range(1,51)]

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
