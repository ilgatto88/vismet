import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pandas import DataFrame
import datetime
import smtplib
import os

#Actual time
now_time = '{0:%Y-%m-%d}'.format(datetime.datetime.now())

#Counting errors
error_count = 0
error_msg = 'Errors, if any:\n'

#database check parameter
dbcheck = True

#Fetching login data from text file
try:
    cred_list = []
    with open('/home/pi/Documents/logfiles/login_metgrab_database.txt', 'r') as loginfile:
        for item in loginfile.read().split(','):
            cred_list.append(item)

    user = cred_list[0]
    pword = cred_list[1]

	
    #Connecting to the PostgreSQL database
    dsn = "dbname='met_project' user='"+user+"' host = 'localhost' password='"+pword+"'"
    conn = psycopg2.connect(dsn)
    print('Successful login!')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    # Define a cursor to work with
    cur = conn.cursor()
except:
    error_count += 101
    error_msg + ' Database not available!'
    print('Database not available!')
    dbcheck = False

#If dbcheck = False, this part won't be executed
if dbcheck:

    #######Fetching OMSZ data#######
    try:
        sql_omsz = "SELECT timeofrequest, Fcst_Tmin_for_day1, Fcst_Tmax_for_day1 FROM omsz_table ORDER BY timeofrequest DESC LIMIT 1;"
        cur.execute(sql_omsz)
        fetched_data_omsz = cur.fetchall()
    except:
        print("Problem with OMSZ data, cannot fetch last row!")
        error_count += 1
        error_msg + 'Cannot fetch OMSZ data! '

    #######Fetching Idokep data#######
    try:
        sql_idokep = "SELECT timeofrequest, Fcst_Tmin_for_day1, Fcst_Tmax_for_day1 FROM idokep_table ORDER BY timeofrequest DESC LIMIT 1;"
        cur.execute(sql_idokep)
        fetched_data_idokep = cur.fetchall()
    except:
        print("Problem with Idokep data, cannot fetch last row!")
        error_count += 1
        error_msg + 'Cannot fetch Időkép data! '

    #######Fetching Koponyeg data#######
    try:
        sql_koponyeg = "SELECT timeofrequest, Fcst_Tmin_for_day1, Fcst_Tmax_for_day1 FROM koponyeg_table ORDER BY timeofrequest DESC LIMIT 1;"
        cur.execute(sql_koponyeg)
        fetched_data_koponyeg = cur.fetchall()
    except:
        print("Problem with Koponyeg data, cannot fetch last row!")
        error_count += 1
        error_msg + 'Cannot fetch Köpönyeg data! '

    #######Fetching Ogimet data#######
    try:
        sql_ogimet = "SELECT timeofrequest, Obs_Tmin, Obs_Tmax FROM ogimet_table ORDER BY timeofrequest DESC LIMIT 1;"
        cur.execute(sql_ogimet)
        fetched_data_ogimet = cur.fetchall()
    except:
        print("Problem with Ogimet data, cannot fetch last row!")
        error_count += 1
        error_msg + 'Cannot fetch Ogimet data! '

    #######Checking date of the last row of omsz_table#######
    if (now_time == fetched_data_omsz[0][0][0:10]) and (fetched_data_omsz[0][1] != None) and (fetched_data_omsz[0][2] != None):
        print('OMSZ OK!')
    else:
        error_count += 1
        error_msg + 'Problem with OMSZ data! '

    #Checking date of the last row of idokep_table#######
    if (now_time == fetched_data_idokep[0][0][0:10]) and (fetched_data_idokep[0][1] != None) and (fetched_data_idokep[0][2] != None):
        print('Idokep OK!')
    else:
        error_count += 1
        error_msg + 'Problem with Időkep data! '

    #Checking date of the last row of koponyeg_table#######
    if (now_time == fetched_data_koponyeg[0][0][0:10]) and (fetched_data_koponyeg[0][1] != None) and (fetched_data_koponyeg[0][2] != None):
        print('Koponyeg OK!')
    else:
        error_count += 1
        error_msg + 'Problem with Köpönyeg data! '

    #Checking date of the last row of ogimet_table#######
    if (now_time == fetched_data_ogimet[0][0][0:10]) and (fetched_data_ogimet[0][1] != None) and (fetched_data_ogimet[0][2] != None):
        print('Ogimet OK!')
    else:
        error_count += 1
        error_msg + 'Problem with Ogimet data! '

print('Number of errors: ' + str(error_count))

## SENDING WARNING MAIL ONLY IF error_count > 0!
if error_count > 0:

    #Fetching login data from text file
    cred_list_gmail = []
    with open('/home/pi/Documents/logfiles/login_gmail.txt', 'r') as loginfile_gmail:
        for item in loginfile_gmail.read().split(','):
            cred_list_gmail.append(item)

    mail = cred_list_gmail[0]
    mail_pword = cred_list_gmail[1]

    send_to = cred_list_gmail[0]
    mail_subject = 'metgrab.py warning message'
    if error_count < 100:
        mail_text = 'Database is missing some data, please check it!\nNumber of wrong or incomplete tables: ' + str(error_count) + '\n' + error_msg
    else:
        mail_text = 'Database connection problem!'

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
    print('Warning e-mail sent')

    smtpObj.quit()

else:
    print('Starting vismet.py...')
    os.system('python3 /home/pi/learning_python/vismet/vismet.py')