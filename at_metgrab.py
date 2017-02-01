# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup   # for web scraping
import urllib.request           # loading website
import datetime                 # actual date, comparing dates
import re                       # regular expressions
from pandas import DataFrame    # for creating dataframes


#Actual time
now_time = '{0:%Y-%m-%d %H:%M}'.format(datetime.datetime.now())

# Date today, datetime and str formats
date_today = datetime.date.today()
str_date_today = (datetime.date.today()).strftime('%Y-%m-%d')

# Date tomorrow, datetime and str formats
date_tomorrow = date_today + datetime.timedelta(days=1)
str_date_tomorrow = (date_tomorrow).strftime('%Y-%m-%d')

def ubimet_scrape():

    try:
        # Basic url
        url = 'http://wetter.tv/wien/morgen'

        # Create Beautiful Soup data, this will allow us to easily search for data on the webpage
        soup = BeautifulSoup(urllib.request.urlopen(url).read(), 'lxml')

        # Get city name
        city = re.findall('Wetter (.*?) Morgen', soup.find_all('title')[0].text)[0]

        # Get date
        date_soup = soup.find("div", {"class":"slide top-data tomorrow"})['data-day']
        date = date_soup[0:4]+'-'+date_soup[4:6]+'-'+date_soup[6:8]

        # Extracting Tmin from the website
        tmin_soup = soup.findAll('span', class_='temperature-min')[0].text
        tmin_dec = tmin_soup.encode('ascii', 'ignore').decode('ascii')
        tmin = int(tmin_dec.replace(" ", "").replace("C", ""))

        # Extracting Tmax from the website
        tmax_soup = soup.findAll('span', class_='temperature')[0].text
        tmax_dec = tmax_soup.encode('ascii', 'ignore').decode('ascii')
        tmax = int(tmax_dec.replace(" ", "").replace("C", ""))

        if str_date_tomorrow == date:
            tMinMax_df = [ now_time, 'ubimet_fcst_for_day1', 'UBIMET',
                                str_date_tomorrow, city, tmin, tmax ]

        else:
            tMinMax_df = [ now_time, 'ubimet_fcst_for_day1', None, None, None, None, None ]
            print('Problem with UBIMET data, None values inserted.')

    except:
        tMinMax_df = [ now_time, 'ubimet_fcst_for_day1', None, None, None, None, None ]
        print('Problem with UBIMET data, None values inserted.')


    return tMinMax_df


def zamg_scrape():

    try:
        # Basic url
        url = 'https://www.zamg.ac.at/cms/de/wetter/wetter-oesterreich/wien/morgen_vormittag'

        # Create Beautiful Soup data, this will allow us to easily search for data on the webpage
        soup = BeautifulSoup(urllib.request.urlopen(url).read(), 'lxml')

        # Get city name
        city_dec = soup.find_all('title')[0].encode('utf-8').decode('ascii', 'ignore')
        city = re.findall('<title>(.*?) ZAMG', city_dec)[0].replace(" ", "")

        # Extracting Tmin from the website
        tmin_soup = soup.findAll('div', {"id":"oltemp_eins_wien"})[0].encode('utf-8').decode('ascii', 'ignore')
        tmin = int(re.findall('Min:(.*?)/', tmin_soup)[0])

        # Extracting Tmax from the website
        tmax_soup = soup.findAll('div', {"id":"oltemp_eins_wien"})[0].encode('utf-8').decode('ascii', 'ignore')
        tmax = int(re.findall('/Max:(.*?)">', tmax_soup)[0])

        tMinMax_df = [ now_time, 'zamg_fcst_for_day1', 'ZAMG',
                            str_date_tomorrow, city, tmin, tmax ]

    except:
        tMinMax_df = [ now_time, 'zamg_fcst_for_day1', None, None, None, None, None ]
        print('Problem with ZAMG data, None values inserted.')

    return tMinMax_df


def wetterat_scrape():

    try:
        # Basic url
        url = 'http://www.wetter.at/wetter/oesterreich/wien/innere-stadt/prognose/morgen#detail'

        # Create Beautiful Soup data, this will allow us to easily search for data on the webpage
        soup = BeautifulSoup(urllib.request.urlopen(url).read(), 'lxml')

        # Get city name
        city = re.findall('/oesterreich/(.*?)/', url)[0].title()

        # Get date
        date_soup = soup.find("div", class_="daypartnameDetail").text
        date = date_soup[6:10]+'-'+date_soup[3:5]+'-'+date_soup[0:2]
        
        # Extracting Tmin from the website
        tmin_soup = soup.findAll('div', class_='b')[0].encode('utf-8').decode('ascii', 'ignore')
        tmin = int(re.findall('>(.*?) ', tmin_soup)[0])

        # Extracting Tmax from the website
        tmax_soup = soup.findAll('div', class_='b')[0].encode('utf-8').decode('ascii', 'ignore')
        tmax = int(re.findall(' \w| (.*?)</', tmax_soup)[1].replace("|", "").replace(" ", ""))

        if str_date_tomorrow == date:
            tMinMax_df = [ now_time, 'wetter_at_fcst_for_day1', 'WETTER_AT',
                            str_date_tomorrow, city, tmin, tmax ]

        else:
            tMinMax_df = [ now_time, 'wetter_at_fcst_for_day1', None, None, None, None, None ]
            print('Problem with Wetter.at data, None values inserted.')

    except:
        tMinMax_df = [ now_time, 'wetter_at_fcst_for_day1', None, None, None, None, None ]
        print('Problem with Wetter.at data, None values inserted.')

    return tMinMax_df

