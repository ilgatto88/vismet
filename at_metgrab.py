# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup   # for web scraping
import urllib.request           # loading website
import datetime                 # actual date, comparing dates
import re                       # regular expressions
from pandas import DataFrame    # for creating dataframes
import psycopg2                 # connecting to the postgreSQL database
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT      # connecting to the postgreSQL database
import smtplib                  # sending e-mail


# Start writing the logfile
logfile_txt = []
logfile_txt.append('**********************************')

#Actual time
now_time = '{0:%Y-%m-%d %H:%M}'.format(datetime.datetime.now())

# Date today, datetime and str formats
date_today = datetime.date.today()
str_date_today = (datetime.date.today()).strftime('%Y-%m-%d')

# Date tomorrow, datetime and str formats
date_tomorrow = date_today + datetime.timedelta(days=1)
str_date_tomorrow = (date_tomorrow).strftime('%Y-%m-%d')

logfile_txt.append('Script started at:')
logfile_txt.append(str(now_time))

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
            logfile_txt.append('\nProblem with UBIMET data!')

    except:
        tMinMax_df = [ now_time, 'ubimet_fcst_for_day1', None, None, None, None, None ]
        print('Problem with UBIMET data, None values inserted.')
        logfile_txt.append('Problem with UBIMET data, None values inserted.')


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
        logfile_txt.append('Problem with ZAMG data, None values inserted.')

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
            logfile_txt.append('Problem with Wetter.at data, None values inserted.')

    except:
        tMinMax_df = [ now_time, 'wetter_at_fcst_for_day1', None, None, None, None, None ]
        print('Problem with Wetter.at data, None values inserted.')
        logfile_txt.append('Problem with Wetter.at data, None values inserted.')

    return tMinMax_df

def ogimet_scrape():

    # Creating the url for the request. Data from Ogimet for TMAX!, 1 day prior to the day of the scraping day.
    # For TMIN, use the actual day

    str_date_today = str(datetime.date.today()).replace('-', '')
    str_date_today_sima = str(datetime.date.today())

    str_date_yesterday = str(datetime.date.today() + datetime.timedelta(days=-1)).replace('-', '')
    str_date_yesterday_sima = str(datetime.date.today() + datetime.timedelta(days=-1))


    url_ogimet_Tmin = 'http://www.ogimet.com/cgi-bin/getsynop?block=11035&begin=' + str_date_today \
                      + '0600&end=' + str_date_today + '0600'

    url_ogimet_Tmax = 'http://www.ogimet.com/cgi-bin/getsynop?block=11035&begin=' + str_date_yesterday \
                      + '1800&end=' + str_date_yesterday + '1800'

    ogimet_city = 'Wien'

    ###########################___TMIN___##########################
    try:
        page_Tmin = urllib.request.urlopen(url_ogimet_Tmin).read()
        soup_Tmin = BeautifulSoup(page_Tmin, 'lxml')

        soupfile_Tmin = soup_Tmin.find('p').getText()
        synop_code_Tmin = (soupfile_Tmin.strip('\n')[soupfile_Tmin.strip('\n').index(' 333'):])[5:10]

        global synop_Tmin
        if synop_code_Tmin[1] == '0':
            synop_Tmin = synop_code_Tmin[2:4] + '.' + synop_code_Tmin[4:5]

        elif synop_code_Tmin[1] == '1':
            synop_Tmin = '-' + synop_code_Tmin[2:4] + '.' + synop_code_Tmin[4:5]

        Tmin = int(round(float(synop_Tmin)))

    ###########################___TMAX___############################
        page_Tmax = urllib.request.urlopen(url_ogimet_Tmax).read()
        soup_Tmax = BeautifulSoup(page_Tmax, 'lxml')

        soupfile_Tmax = soup_Tmax.find('p').getText()
        synop_code_Tmax = (soupfile_Tmax.strip('\n')[soupfile_Tmax.strip('\n').index(' 333'):])[5:10]

        global synop_Tmax
        if synop_code_Tmax[1] == '0':
            synop_Tmax = synop_code_Tmax[2:4] + '.' + synop_code_Tmax[4:5]

        elif synop_code_Tmax[1] == '1':
            synop_Tmax = '-' + synop_code_Tmax[2:4] + '.' + synop_code_Tmax[4:5]

        Tmax = int(round(float(synop_Tmax)))


        tMinMax_df = [ now_time, 'ogimet_obs_data', 'Ogimet', ogimet_city,
                          str_date_today_sima, Tmin, str_date_yesterday_sima, Tmax ]
    except:
        tMinMax_df = [ now_time, 'ogimet_obs_data', None, None, None, None, None, None ]
        print('Problem with Ogimet data, None values inserted.')
        logfile_txt.append('Problem with Ogimet data, None values inserted.')

    return tMinMax_df

try:
    # Fetching login data from text file
    cred_list = []
    with open('/home/pi/Documents/logfiles/login_metgrab_database.txt', 'r') as loginfile:
        for item in loginfile.read().split(','):
            cred_list.append(item)

    user = cred_list[0]
    pword = cred_list[1]
except:
    print('Username or password incorrect!')


# Connect to the PostgreSQL database
try:
    dsn = "dbname='met_project' user='"+user+"' host = 'localhost' password='"+pword+"'"
    conn = psycopg2.connect(dsn)
    print('Successful login!')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    logfile_txt.append('OK: Successful login to met_project database')
    cur = conn.cursor()

except:
    print('Unable to connect to the database!')
    logfile_txt.append('ERROR: Unable to connect to the database.')


# Inserting data into the SQL table
provider_list = {'ubimet': ubimet_scrape(),
                'zamg': zamg_scrape(),
                'wetter_at': wetterat_scrape()
                }
for prov in provider_list:
    try:
        sql_text = "INSERT INTO "+prov+"_table (TimeOfRequest, DataType, Provider, Fcst_Date, Fcst_City, Fcst_Tmin_for_day1, Fcst_Tmax_for_day1) VALUES (%s, %s, %s, %s, %s, %s, %s);"
        data = tuple(provider_list[prov])
        cur.execute(sql_text, data)
        print(prov+" data succesfully inserted into "+prov+"_table.")
        logfile_txt.append('OK: '+prov+' data successfully inserted into '+prov+'_table.')

    except:
        print("Problem with "+prov+" data, not inserted into "+prov+"_table.")
        sql_text_error = "INSERT INTO "+prov+"_table (TimeOfRequest, DataType, Provider, Fcst_Date, Fcst_City, Fcst_Tmin_for_day1, Fcst_Tmax_for_day1) VALUES (%s, %s, %s, %s, %s, %s, %s);"
        error_data = (now_time, None, None, None, None, None, None)
        cur.execute(sql_text_error, error_data)
        logfile_txt.append('ERROR: '+prov+' data not inserted into '+prov+'_table.')

# Inserting Ogimet data into the table
try:
    sql_ogimet = "INSERT INTO ogimet_wien_table (TimeOfRequest, DataType, Provider, Obs_City, Tmin_Date, Obs_Tmin, Tmax_Date, Obs_Tmax) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
    ogimet_data = tuple(ogimet_scrape())
    cur.execute(sql_ogimet, ogimet_data)
    print('Ogimet Wien data succesfully inserted into ogimet_wien_table.')
    logfile_txt.append('OK: Ogimet Wien data successfully inserted into ogimet_wien_table.')

except:
    print("Problem with Ogimet Wien data, not inserted into ogimet_wien_table!")
    sql_ogimet_error = "INSERT INTO ogimet_wien_table (TimeOfRequest, DataType, Provider, Obs_City, Tmin_Date, Obs_Tmin, Tmax_Date, Obs_Tmax) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
    ogimet_error_data = (now_time, None, None, None, None, None, None, None)
    cur.execute(sql_ogimet_error, ogimet_error_data)
    logfile_txt.append('ERROR: Problem with Ogimet Wien data, not inserted into ogimet_wien_table!')


## END OF THE MAIN SCRIPT ##
## SENDING MAIL ABOUT LOGGED INFORMATION ##
# ONLY IF logfile_txt contains 'Unable' or 'Problem'
if any('Unable' in s for s in logfile_txt) or any('Problem' in s for s in logfile_txt):

    #Fetching login data from text file
    cred_list_gmail = []
    with open('/home/pi/Documents/logfiles/login_gmail.txt', 'r') as loginfile_gmail:
        for item in loginfile_gmail.read().split(','):
            cred_list_gmail.append(item)

    mail = cred_list_gmail[0]
    mail_pword = cred_list_gmail[1]

    send_to = cred_list_gmail[0]
    mail_subject = 'metgrab Wien log message'
    mail_text = "\n".join(logfile_txt)

    #GMail creditentials
    gmail_sender = cred_list_gmail[0]
    gmail_passwd = cred_list_gmail[1]

    #Create connection to GMail service
    smtpObj = smtplib.SMTP('smtp.gmail.com', 587)
    smtpObj.ehlo()
    smtpObj.starttls()
    smtpObj.login(gmail_sender, gmail_passwd)

    mail_body = '\r\n'.join([
        'To: %s' % send_to,
        'From: %s' % gmail_sender,
        'Subject: %s' % mail_subject,
        '',
        mail_text
        ])

    #Sending the mail
    smtpObj.sendmail(gmail_sender, [send_to], mail_body)
    print('Email sent')

    smtpObj.quit()

with open('/home/pi/Documents/logfiles/metgrab__wien_logfile.txt', 'a') as logger:
    for i in logfile_txt:
        logger.write(i+'\n')