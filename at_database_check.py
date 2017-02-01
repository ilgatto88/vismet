import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from pandas import DataFrame
import datetime
import smtplib

#Actual time
now_time = '{0:%Y-%m-%d}'.format(datetime.datetime.now())

#Counting errors
error_count = 0
error_msg = []
error_msg.append('Errors, if any:')

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
    error_msg.append('Database not available!')
    print('Database not available!')
    dbcheck = False


fetched_data_ubimet = []
fetched_data_zamg = []
fetched_data_wetterat = []

provider_list = {'ubimet': fetched_data_ubimet,
                'zamg': fetched_data_zamg,
                'wetter_at': fetched_data_wetterat
                }

#If dbcheck = False, this part won't be executed
if dbcheck:
    #######Fetching and checking provider data#######
    for prov in provider_list:
        try:
            sql_text = "SELECT timeofrequest, Fcst_Tmin_for_day1, Fcst_Tmax_for_day1 FROM "+prov+"_table ORDER BY timeofrequest DESC LIMIT 1;"
            cur.execute(sql_text)
            provider_list[prov] = cur.fetchall()

            if (now_time == provider_list[prov][0][0][0:10]) and (provider_list[prov][0][1] != None) and (provider_list[prov][0][2] != None):
                print(prov+' OK!')
            else:
                error_count += 1
                error_msg.append('Problem with '+prov+' data!')

        except:
            print("Problem with "+prov+" data, cannot fetch last row!")
            error_count += 1
            error_msg.append("Cannot fetch "+prov+" data!")


    #######Fetching Ogimet data#######
    try:
        sql_ogimet = "SELECT timeofrequest, Obs_Tmin, Obs_Tmax FROM ogimet_wien_table ORDER BY timeofrequest DESC LIMIT 1;"
        cur.execute(sql_ogimet)
        fetched_data_ogimet_wien = cur.fetchall()

        if (now_time == fetched_data_ogimet_wien[0][0][0:10]) and (fetched_data_ogimet_wien[0][1] != None) and (fetched_data_ogimet_wien[0][2] != None):
            print('Ogimet Wien OK!')

        else:
            error_count += 1
            error_msg.append('Problem with Ogimet Wien data! ')
    except:
        print("Problem with Ogimet Wien data, cannot fetch last row!")
        error_count += 1
        error_msg.append('Cannot fetch Ogimet Wien data!')


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
    mail_subject = 'database AT warning message'
    if error_count < 100:
        mail_text = 'Database AT is missing some data, please check it!\nNumber of wrong or incomplete tables: ' + str(error_count) + '\n' + '\n'.join(error_msg) + '\nDiagram has not been drawn.'
    else:
        mail_text = 'Database AT connection problem!' + '\n'.join(error_msg) + '\nDiagram has not been drawn.'

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
    with open('/home/pi/working_python/metgrab/at_database_check_output.txt', 'w') as textfile:
        textfile.write('0')

else:
    with open('/home/pi/working_python/metgrab/at_database_check_output.txt', 'w') as textfile:
        textfile.write('1')