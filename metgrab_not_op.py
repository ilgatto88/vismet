# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import urllib.request
import datetime
from pandas import DataFrame
import csv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import smtplib

"""
# Date today, datetime and str formats
date_today = datetime.date.today()
str_date_today = (datetime.date.today()).strftime('%Y-%m-%d')

# Date tomorrow, datetime and str formats
date_tomorrow = date_today + datetime.timedelta(days=1)
str_date_tomorrow = (date_today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
"""

#Actual time
now_time = '{0:%Y-%m-%d %H:%M}'.format(datetime.datetime.now())

#This is the header of the dataframe. It only has to be used once at the beginning.
mycolumns = ['TimeOfRequest',
             'DataType', 'Provider', 'Fcst_Date', 'Fcst_City', 'Fcst_Tmin_for_day1', 'Fcst_Tmax_for_day1',
             'DataType', 'Provider', 'Fcst_Date', 'Fcst_City', 'Fcst_Tmin_for_day1', 'Fcst_Tmax_for_day1',
             'DataType', 'Provider', 'Fcst_Date', 'Fcst_City', 'Fcst_Tmin_for_day1', 'Fcst_Tmax_for_day1',
             'DataType', 'Provider', 'Obs_City', 'Tmin_Date', 'Obs_Tmin', 'Tmax_Date', 'Obs_Tmax']

# Start writing the logfile
logfile_text = "\n".join(['Script started at:', str(now_time)])


def omsz_scrape():

    # With this script you can scrabe data from the webpage of the Hungarian Weather Service (OMSZ)
    # It collects the date, the city name, the forecasted minimum and maximum temperature.
    # The output is a list, containing the DataType id, Provider (OMSZ), date of the forecast, city and
    # the two temperature parameters. They can only be integer numbers.


    # Date today, datetime and str formats
    date_today = datetime.date.today()
    str_date_today = (datetime.date.today()).strftime('%Y-%m-%d')

    # Date tomorrow, datetime and str formats
    date_tomorrow = date_today + datetime.timedelta(days=1)
    str_date_tomorrow = (date_tomorrow).strftime('%Y-%m-%d')


    url_omsz = 'http://met.hu/idojaras/elorejelzes/kozeptavu_elorejelzes/main.php?c=tablazat&v=Budapest'

    # At first we create a Beautiful Soup data, this will allow us to easily search for data on the webpage
    page = urllib.request.urlopen(url_omsz).read()
    soup = BeautifulSoup(page, 'lxml')

    # Get city name
    omsz_city = soup.find_all('option', class_='akt')[1].text


    # The month and day from the first line of the data table. Months has to be converted: 'november' -> 11
    omsz_date = (soup.find_all('th', class_='rbg0')[0].get_text()).split()

    # Dictionary for months
    months = {'január': '01', 'február': '02', 'március': '03', 'április': '04', 'május': '05',
            'június': '06', 'július': '07', 'augusztus': '08', 'szeptember': '09', 'október': '10',
            'november': '11', 'december': '12'}

    # Grab the actual date from the OMSZ webpage. First the year, the month and day is taken
    # from the line from where I take the chosen values!
    omsz_table_actual_year = (soup.find_all('option', class_='akt')[0].get_text())[:4]
    omsz_table_first_month = ''.join(map(str, [value for month, value in months.items() if month == omsz_date[0]]))
    omsz_table_first_day = omsz_date[1].strip('.')

    if len(omsz_table_first_day) == 1:
        omsz_table_first_day = '0' + omsz_table_first_day

    # The first date of the data table in str format
    str_omsz_actual_first_date = '-'.join([omsz_table_actual_year, omsz_table_first_month, omsz_table_first_day])
    omsz_actual_first_date = datetime.datetime.strptime(str_omsz_actual_first_date, '%Y-%m-%d').date()

    # Creating an empty dataframe to store the data # Not necessary
    #tMinMax_omsz_df = DataFrame(columns=mycolumns)

    # If omsz actual date is equal with today's date, then take the value from the second row of the table ->
    # to have the forecast for the next day


    if str_date_today == str_omsz_actual_first_date:
        tMinMax_omsz_df = [ now_time,
                       'omsz_fcst_for_day1', 'OMSZ', str_date_tomorrow, omsz_city,
                        str(soup.find_all('td', class_='T N rbg1')[0].get_text()),
                        str(soup.find_all('td', class_='T X rbg1')[0].get_text()) ]


    # If there is a one day difference between the actual date and the omsz actual date, then
    # take the value from the first row of the table. Normally it shouldn't happen!
    elif str(omsz_actual_first_date - date_today) == '1 day, 0:00:00':
        tMinMax_omsz_df = [ now_time,
                       'omsz_fcst_for_day1', 'OMSZ', str_date_tomorrow, omsz_city,
                        str(soup.find_all('td', class_='T N rbg0')[0].get_text()),
                        str(soup.find_all('td', class_='T X rbg0')[0].get_text()) ]


    return tMinMax_omsz_df


def idokep_scrape():

    # Date today, datetime and str formats
    date_today = datetime.date.today()

    # Date tomorrow, datetime and str formats
    date_tomorrow = date_today + datetime.timedelta(days=1)
    str_date_tomorrow = (date_tomorrow).strftime('%Y-%m-%d')

    url_idokep = 'http://www.idokep.hu/elorejelzes/Budapest'

    # At first we create a Beautiful Soup data, this will allow us to easily search for data on the webpage
    page = urllib.request.urlopen(url_idokep).read()
    soup = BeautifulSoup(page, 'lxml')

    # Dictionary for months, difference between the OMSZ version: first letter is uppercase
    months_M = {'Január': '01', 'Február': '02', 'Március': '03', 'Április': '04', 'Május': '05',
              'Június': '06', 'Július': '07', 'Augusztus': '08', 'Szeptember': '09', 'Október': '10',
              'November': '11', 'December': '12'}


    # Idokep-like month + day in str format
    month_tomorrow = str_date_tomorrow[5:7]

    if str_date_tomorrow[-2:-1] == '0':
        str_date_tomorrow1 = str_date_tomorrow[-1]
    else:
        str_date_tomorrow1 = str_date_tomorrow[-2:]

    text_month_tomorrow_idokep = list(map(str, [key for key, value in months_M.items() if
                                value == month_tomorrow]))[0] + ' ' + str_date_tomorrow1 + '.'


    # Get city: because the url contains the city name, it will be always Budapest. We could take it from the
    # url too, of course
    idokep_city = 'Budapest'

    # This list will contains all the temperature forecasts
    lst = []
    for hit in soup.findAll('div', attrs={'class': "buborek-text"}):
        lst.append(hit.text)


    global idokep_Tmin_tomorrow
    #Scrape Tmin for tomorrow in the previous list
    for min in lst:
        if text_month_tomorrow_idokep in min and 'Minimum' in min:
            idokep_Tmin_tomorrow = (min[21:].split(' '))[0]

    global idokep_Tmax_tomorrow
    # Scrape Tmax for tomorrow in the previous list (same approach as with Tmin)
    for max in lst:
        if text_month_tomorrow_idokep in max and 'Maximum' in max:
            idokep_Tmax_tomorrow = (max[21:].split(' '))[0]


    # Creating an empty dataframe for the final values + adding the values into the dataframe
    tMinMax_idokep_df = DataFrame(columns=mycolumns)
    tMinMax_idokep_df = [ now_time, 'idokep_fcst_for_day1', 'Idokep', str_date_tomorrow, idokep_city,
                         idokep_Tmin_tomorrow, idokep_Tmax_tomorrow ]


    return tMinMax_idokep_df

def koponyeg_scrape():

    # Date today, datetime and str formats
    date_today = datetime.date.today()

    # Date tomorrow, datetime and str formats
    str_date_tomorrow = (date_today + datetime.timedelta(days=1)).strftime('%Y-%m-%d')


    url_koponyeg = 'http://koponyeg.hu/t/Budapest'


    page = urllib.request.urlopen(url_koponyeg).read()
    soup = BeautifulSoup(page, 'lxml')

    months_short = {'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'maj': '05',
                    'jun': '06', 'jul': '07', 'aug': '08', 'szep': '09', 'okt': '10',
                    'nov': '11', 'dec': '12'}

    # Get city name
    koponyeg_city = 'Budapest'

    koponyeg_year = (soup.find('span', attrs={'id': "headerdate_sticky"})).text[:4]


    lst_month = []
    for date in soup.findAll('div', attrs={'class': "honap"}):
        lst_month.append(date.text)


    lst_day1 = []
    for date in soup.findAll('div', attrs={'class': "nap"}):
        lst_day1.append(date.text)


    lst_day = []
    for n in lst_day1:
        if len(n) == 1:
            day = '0' + n
            lst_day.append(day)
        else:
            lst_day.append(n)


    lst_month_day = []
    for n in range(len(lst_day)):
        lst_month_day.append(lst_month[n] + ' ' + lst_day[n])


    #Building the date of tomorrow

    koponyeg_month_tomorrow = list(map(str, [value for key, value in months_short.items()
                                            if key == lst_month_day[1][0:3]]))


    if ''.join(koponyeg_month_tomorrow) == '01' and lst_month_day[1].split()[1] == '01':
        koponyeg_year = str(int(koponyeg_year) + 1)
        koponyeg_DATE_tomorrow = koponyeg_year + '-' + ''.join(koponyeg_month_tomorrow)\
                                 + '-' + lst_month_day[1].split()[1]
    else:
        koponyeg_DATE_tomorrow = koponyeg_year + '-' + ''.join(koponyeg_month_tomorrow)\
                                 + '-' + lst_month_day[1].split()[1]


    lst_min = []
    for hit in soup.findAll('div', attrs={'class': "min_15napos"}):
        lst_min.append(hit.text.strip('\n').strip('°C'))


    global min_tomorrow
    if koponyeg_DATE_tomorrow == str_date_tomorrow:
        min_tomorrow = lst_min[1][22:]

    lst_max = []
    for hit in soup.findAll('div', attrs={'class': "max_15napos"}):
        lst_max.append(hit.text.strip('\n').strip('°C'))


    global max_tomorrow
    if koponyeg_DATE_tomorrow == str_date_tomorrow:
        max_tomorrow = lst_max[1][22:]


    tMinMax_koponyeg_df = [ now_time, 'koponyeg_fcst_for_day1', 'Koponyeg', str_date_tomorrow, koponyeg_city,
                            min_tomorrow, max_tomorrow]


    return tMinMax_koponyeg_df


def ogimet_scrape():


    # Creating the url for the request. Data from Ogimet for TMAX!, 1 day prior to the day of scrape day.
    # For TMIN, use the day of the scraping

    str_date_today = str(datetime.date.today()).replace('-', '')
    str_date_today_sima = str(datetime.date.today())

    str_date_yesterday = str(datetime.date.today() + datetime.timedelta(days=-1)).replace('-', '')
    str_date_yesterday_sima = str(datetime.date.today() + datetime.timedelta(days=-1))

    url_ogimet_Tmin = 'http://www.ogimet.com/cgi-bin/getsynop?block=12843&begin=' + str_date_today \
                      + '0600&end=' + str_date_today + '0600'

    url_ogimet_Tmax = 'http://www.ogimet.com/cgi-bin/getsynop?block=12843&begin=' + str_date_yesterday \
                      + '1800&end=' + str_date_yesterday + '1800'

    ogimet_city = 'Budapest'


    ###########################___TMIN___##########################
    try:
        page_Tmin = urllib.request.urlopen(url_ogimet_Tmin).read()
        soup_Tmin = BeautifulSoup(page_Tmin, 'lxml')


        soupfile_Tmin = soup_Tmin.find('p').getText()
        synop_code_Tmin = (soupfile_Tmin.strip('\n')[soupfile_Tmin.strip('\n').index('333'):])[4:9]


        global synop_Tmin

        if synop_code_Tmin[1] == '0':
            synop_Tmin = synop_code_Tmin[2:4] + '.' + synop_code_Tmin[4:5]

        elif synop_code_Tmin[1] == '1':
            synop_Tmin = '-' + synop_code_Tmin[2:4] + '.' + synop_code_Tmin[4:5]


        Tmin = int(round(float(synop_Tmin)))
    
    except:
        Tmin = None


    ###########################___TMAX___############################
    try:
        page_Tmax = urllib.request.urlopen(url_ogimet_Tmax).read()
        soup_Tmax = BeautifulSoup(page_Tmax, 'lxml')

        soupfile_Tmax = soup_Tmax.find('p').getText()
        synop_code_Tmax = (soupfile_Tmax.strip('\n')[soupfile_Tmax.strip('\n').index('333'):])[4:9]

        global synop_Tmax

        if synop_code_Tmax[1] == '0':
            synop_Tmax = synop_code_Tmax[2:4] + '.' + synop_code_Tmax[4:5]

        elif synop_code_Tmax[1] == '1':
            synop_Tmax = '-' + synop_code_Tmax[2:4] + '.' + synop_code_Tmax[4:5]


        Tmax = int(round(float(synop_Tmax)))

    except:
        Tmax = None

    tMinMax_ogimet_df = [ now_time, 'ogimet_obs_data', 'Ogimet', ogimet_city,
                          str_date_today_sima, Tmin, str_date_yesterday_sima, Tmax ]


    return tMinMax_ogimet_df


#Fetching login data from text file
cred_list = []
with open('/home/pi/Documents/logfiles/login_metgrab_database.txt', 'r') as loginfile:
    for item in loginfile.read().split(','):
        cred_list.append(item)

user = cred_list[0]
pword = cred_list[1]
	
#Try to connect to the PostgreSQL database
try:
	dsn = "dbname='met_project' user='"+user+"' host = 'localhost' password='"+pword+"'"
	conn = psycopg2.connect(dsn)
	print('Successful login!')
	conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
	logfile_text = "\n".join([logfile_text, 'OK: Successful login to met_project database'])

except Exception as e1:
    print(str(e1))
    print('Unable to connect to the database!')
    print('Data will be written into the grabbed.csv file!')
    logfile_text = "\n".join([logfile_text, 'ERROR: Unable to connect to the database', 'Problem description:', str(e1), 'Data will be written into the grabbed.csv file!'])

    def Main():

        new_list = omsz_scrape() + idokep_scrape()[1:] + koponyeg_scrape()[1:] + ogimet_scrape()[1:]
        with open('/home/pi/Documents/python_projects/metgrab/grabbed.csv', 'a') as csvfile:
            csv_write = csv.writer(csvfile, dialect='excel', delimiter=';')

            #csv_write.writerows([mycolumns]) #If there is no header at the beginning
            csv_write.writerows([new_list])
        return

    print('Data successfully written into the csv file.')
    logfile_text = "\n".join([logfile_text, 'Data successfully writte into the csv file.'])


# Define a cursor to work with
cur = conn.cursor()


#Inserting OMSZ data into the table
try:
    sql_omsz = "INSERT INTO omsz_table (TimeOfRequest, DataType, Provider, Fcst_Date, Fcst_City, Fcst_Tmin_for_day1, Fcst_Tmax_for_day1) VALUES (%s, %s, %s, %s, %s, %s, %s);"
    omsz_data = tuple(omsz_scrape())
    cur.execute(sql_omsz, omsz_data)
    print('OMSZ data succesfully inserted into omsz_table.')
    logfile_text = "\n".join([logfile_text, 'OK: OMSZ data successfully inserted into omsz_table.'])

#    cur.execute("SELECT * FROM omsz_table;")
#    print(cur.fetchall())

except:
    print("Problem with OMSZ data, not inserted into omsz_table!")
    sql_omsz_error = "INSERT INTO omsz_table (TimeOfRequest) VALUES (%s);"
    cur.execute(sql_omsz_error, now_time)
    logfile_text = "\n".join([logfile_text, 'ERROR: Problem with OMSZ data, not inserted into omsz_table!'])

#Inserting Idokep data into the table
try:
    sql_idokep = "INSERT INTO idokep_table (TimeOfRequest, DataType, Provider, Fcst_Date, Fcst_City, Fcst_Tmin_for_day1, Fcst_Tmax_for_day1) VALUES (%s, %s, %s, %s, %s, %s, %s);"
    idokep_data = tuple(idokep_scrape())
    cur.execute(sql_idokep, idokep_data)
    print('Idokep data succesfully inserted into idokep_table.')
    logfile_text = "\n".join([logfile_text, 'OK: Idokep data successfully inserted into idokep_table.'])

except:
    print("Problem with Idokep data, not inserted into idokep_table!")
    sql_idokep_error = "INSERT INTO idokep_table (TimeOfRequest) VALUES (%s);"
    cur.execute(sql_idokep_error, now_time)
    logfile_text = "\n".join([logfile_text, 'ERROR: Problem with Idokep data, not inserted into idokep_table!'])

#Inserting Koponyeg data into the table
try:
    sql_koponyeg = "INSERT INTO koponyeg_table (TimeOfRequest, DataType, Provider, Fcst_Date, Fcst_City, Fcst_Tmin_for_day1, Fcst_Tmax_for_day1) VALUES (%s, %s, %s, %s, %s, %s, %s);"
    koponyeg_data = tuple(koponyeg_scrape())
    cur.execute(sql_koponyeg, koponyeg_data)
    print('Koponyeg data succesfully inserted into idokep_table.')
    logfile_text = "\n".join([logfile_text, 'OK: Koponyeg data successfully inserted into koponyeg_table.'])

except:
    print("Problem with Koponyeg data, not inserted into koponyeg_table!")
    sql_koponyeg_error = "INSERT INTO koponyeg_table (TimeOfRequest) VALUES (%s);"
    cur.execute(sql_koponyeg_error, now_time)
    logfile_text = "\n".join([logfile_text, 'ERROR: Problem with Koponyeg data, not inserted into koponyeg_table!'])

#Inserting Ogimet data into the table
try:
    sql_ogimet = "INSERT INTO ogimet_table (TimeOfRequest, DataType, Provider, Obs_City, Tmin_Date, Obs_Tmin, Tmax_Date, Obs_Tmax) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);"
    ogimet_data = tuple(ogimet_scrape())
    cur.execute(sql_ogimet, ogimet_data)
    print('Ogimet data succesfully inserted into ogimet_table.')
    logfile_text = "\n".join([logfile_text, 'OK: Ogimet data successfully inserted into ogimet_table.'])

except:
    print("Problem with Ogimet data, not inserted into ogimet_table!")
    sql_ogimet_error = "INSERT INTO ogimet_table (TimeOfRequest) VALUES (%s);"
    cur.execute(sql_ogimet_error, now_time)
    logfile_text = "\n".join([logfile_text, 'ERROR: Problem with Ogimet data, not inserted into ogimet_table!'])



## END OF THE MAIN SCRIPT ##
## SENDING MAIL ABOUT LOGGED INFORMATION ##

#Fetching login data from text file
cred_list_gmail = []
with open('/home/pi/Documents/logfiles/login_gmail.txt', 'r') as loginfile_gmail:
    for item in loginfile_gmail.read().split(','):
        cred_list_gmail.append(item)

mail = cred_list_gmail[0]
mail_pword = cred_list_gmail[1]

send_to = cred_list_gmail[0]
mail_subject = 'metgrab.py log message'
mail_text = logfile_text

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

try:
    smtpObj.sendmail(gmail_sender, [send_to], mail_body)
    print('Email sent')
except:
    print('Error sending email')

smtpObj.quit()

#Writing the log text to the metgrab_logfile.txt in the folder
with open('/home/pi/Documents/logfiles/metgrab_logfile.txt', 'a') as logger:
    logger.write('*************************\n') 
    logger.write(logfile_text)


