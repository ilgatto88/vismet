# -*- coding: utf-8 -*-

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import matplotlib.pyplot as plt
#from matplotlib import style
import matplotlib.ticker as mticker
import pandas as pd
import numpy as np
from taylorDiagram import TaylorDiagram
import math

#General pyplot style can be used, but it makes problems with the Taylor-Diagram!
#style.use('fivethirtyeight')
#Testing....

desired_width = 320
pd.set_option('display.width', desired_width)

#Start of the graphing function
def graph_met():
    fig = plt.figure()

    #Define diagram, subplots
    ax1_left = plt.subplot2grid((4, 10), (0, 0), rowspan=2, colspan=6)
    #plt.title('OMSZ')
    #plt.ylabel('Tmin & Tmax')
    ax2 = plt.subplot2grid((4, 1), (2, 0), rowspan=1, colspan=1)
    #plt.title('Köpönyeg')
    #plt.ylabel('Tmin & Tmax')
    ax3 = plt.subplot2grid((4, 1), (3, 0), rowspan=1, colspan=1, sharex=ax2)
    #plt.title('Mért adatok')
    #plt.ylabel('Tmin & Tmax & Avg')
	
    #Fetching login data from text file
    cred_list = []
    with open('/home/pi/Documents/logfiles/login_metgrab_database.txt', 'r') as loginfile:
        for item in loginfile.read().split(','):
            cred_list.append(item)

    user = cred_list[0]
    pword = cred_list[1]

	# Connecting to met_project database, exception
    try:
        database = "dbname = 'met_project' user = '"+user+"' host = 'localhost' password = '"+pword+"'"
        conn = psycopg2.connect(database)
        print('Successful connection.')
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    except Exception as e1:
        print(str(e1))
        print('Unable to connect to met_project database!')

    # Define a cursor to work with
    cur = conn.cursor()

    # Fetching provider data
    sql_get_omsz = "SELECT fcst_date, fcst_tmin_for_day1, fcst_tmax_for_day1 from omsz_table;"
    cur.execute(sql_get_omsz)
    omsz_fetched = pd.DataFrame(cur.fetchall(), columns=['date', 'omsz_tmin', 'omsz_tmax'], dtype=int)

    sql_get_idokep = "SELECT fcst_tmin_for_day1, fcst_tmax_for_day1 from idokep_table;"
    cur.execute(sql_get_idokep)
    idokep_fetched = pd.DataFrame(cur.fetchall(), columns=['idokep_tmin', 'idokep_tmax'])

    sql_get_koponyeg = "SELECT fcst_tmin_for_day1, fcst_tmax_for_day1 from koponyeg_table;"
    cur.execute(sql_get_koponyeg)
    koponyeg_fetched = pd.DataFrame(cur.fetchall(), columns=['koponyeg_tmin', 'koponyeg_tmax'])

    sql_get_ogimet = "SELECT Tmin_date, Obs_Tmin from ogimet_table;"
    cur.execute(sql_get_ogimet)
    ogimet_fetched_uncorrected_tmin = pd.DataFrame(cur.fetchall(), columns=['date', 'ogimet_tmin'])

    sql_get_ogimet = "SELECT Tmax_date, Obs_Tmax from ogimet_table;"
    cur.execute(sql_get_ogimet)
    ogimet_fetched_uncorrected_tmax = pd.DataFrame(cur.fetchall(), columns=['date', 'ogimet_tmax'])

    #Putting provider data into a DataFrame
    frames_prov = [omsz_fetched, idokep_fetched, koponyeg_fetched]
    concat_prov = pd.concat(frames_prov, axis=1)

    merged_ogimet = pd.merge(ogimet_fetched_uncorrected_tmin, ogimet_fetched_uncorrected_tmax, on='date')
    merged_full = pd.merge(concat_prov, merged_ogimet)

    merged_full_NArepl = merged_full.replace(pd.np.nan, 'NA')
    
    #Calculating data for the Taylor Diagram
    #Calculating standard deviation of the observation
    ogimet_stdev = np.std(merged_full['ogimet_tmin']+merged_full['ogimet_tmax'])

    #Create dataframe for correlation calculations
    df_for_corr_omsz = pd.DataFrame({'OMSZ': merged_full['omsz_tmin'].append(merged_full['omsz_tmax']),
                                            'Ogimet': merged_full['ogimet_tmin'].append(merged_full['ogimet_tmax'])})
    df_for_corr_idokep = pd.DataFrame({'Idokep': merged_full['idokep_tmin'].append(merged_full['idokep_tmax']),
                                            'Ogimet': merged_full['ogimet_tmin'].append(merged_full['ogimet_tmax'])})
    df_for_corr_koponyeg = pd.DataFrame({'Koponyeg': merged_full['koponyeg_tmin'].append(merged_full['koponyeg_tmax']),
                                            'Ogimet': merged_full['ogimet_tmin'].append(merged_full['ogimet_tmax'])})

    print(merged_full_NArepl[['date', 'omsz_tmin']])
    list4rmse = []
    for i in range(4, len(merged_full_NArepl[['date', 'omsz_tmin', 'omsz_tmax', 'ogimet_tmin', 'ogimet_tmax']])):
        l1 = []
        for k in range(0,-5,-1):
            if merged_full_NArepl['omsz_tmin'][i+k] != 'NA' and merged_full_NArepl['ogimet_tmin'][i+k] != 'NA':
                l1.append((merged_full_NArepl['omsz_tmin'][i+k]-merged_full_NArepl['ogimet_tmin'][i+k])**2)
            else:
                l1.append(None)
        rmse = round(math.sqrt(sum(filter(lambda i: isinstance(i, float), l1))/5.0), 2)
        #rmse = round(math.sqrt(avg_mse), 2)
        list4rmse.append([merged_full_NArepl['date'][i], rmse])


    print(list4rmse)
    newdf = pd.DataFrame.from_records(list4rmse, columns=['date', 'rmse5day_omsz'])
    print(newdf)

    #Calculating 5 day moving RMSE of providers forecast vs observation
    #for row in merged_full['omsz_tmin']:
        #print(row)

graph_met()

"""
    #Defining sample data (providers stdev, corr and name)
    samples = dict(alap=[[np.std(merged_full['omsz_tmin']+merged_full['omsz_tmax']),
                            round(df_for_corr_omsz.corr()['OMSZ'][1], 4), "OMSZ", '^'],
                         [np.std(merged_full['idokep_tmin'] + merged_full['idokep_tmax']),
                            round(df_for_corr_idokep.corr()['Idokep'][1], 4), "Idokep", '.'],
                         [np.std(merged_full['koponyeg_tmin'] + merged_full['koponyeg_tmax']),
                            round(df_for_corr_koponyeg.corr()['Koponyeg'][1], 4), "Koponyeg", 'o']])

    #Define plotting colors, cm is colormap, Set1 is the first cm set
    colors = plt.matplotlib.cm.Set1(np.linspace(0, 1, len(merged_full['ogimet_tmin'])))

    #Define correlation line coordinates
    r_cir = ogimet_stdev * 1.5
    x10 = [0.05, 1.470] #corr=0.1
    y10 = [0.0, r_cir]
    x20 = [0.05, 1.367] #corr=0.2
    y20 = [0.0, r_cir]
    x30 = [0.05, 1.266] #corr=0.3
    y30 = [0.0, r_cir]
    x40 = [0.05, 1.156] #corr=0.4
    y40 = [0.0, r_cir]
    x50 = [0.05, 1.043] #corr=0.5
    y50 = [0.0, r_cir]
    x60 = [0.05, 0.924] #corr=0.6
    y60 = [0.0, r_cir]
    x70 = [0.05, 0.799] #corr=0.7
    y70 = [0.0, r_cir]
    x80 = [0.05, 0.639] #corr=0.8
    y80 = [0.0, r_cir]
    x90 = [0.05, 0.450] #corr=0.9
    y90 = [0.0, r_cir]

    #Plot correlation lines
    dia = TaylorDiagram.TaylorDiagram(ogimet_stdev, fig=fig, rect=222, label='Observation')
    corr_line_color = "c"
    dia.ax.plot(x10, y10, color=corr_line_color)
    dia.ax.plot(x20, y20, color=corr_line_color)
    dia.ax.plot(x30, y30, color=corr_line_color)
    dia.ax.plot(x40, y40, color=corr_line_color)
    dia.ax.plot(x50, y50, color=corr_line_color)
    dia.ax.plot(x60, y60, color=corr_line_color)
    dia.ax.plot(x70, y70, color=corr_line_color)
    dia.ax.plot(x80, y80, color=corr_line_color)
    dia.ax.plot(x90, y90, color=corr_line_color)


    #markers = dict([('*', 0),(',', 1),('.', 2)])
    #for i in markers.keys():
        #print(i)


    #Plot samples on the Taylor-Diagram
    for i,(stddev,corrcoef,name, marker1) in enumerate(samples['alap']):
        dia.add_sample(stddev, corrcoef,
                       marker=marker1, ms=10, ls='', # marker='$%d$' % (i+1)
                       mfc=colors[i], mec=colors[i], # Colors
                       label=name)


    #Adjust contours, labels and legend
    contours = dia.add_contours(levels=5, colors='0.5') # levels: number of stdev inner circles, colors: 0=white 1=black 0.5=~grey
    dia.ax.clabel(contours, inline=1, fontsize=10, fmt='%.1f') # inline: 1/0 curved line is cut under the numbers, fmt(format)

    #Legend settings
    fig.legend(dia.samplePoints,
               [p.get_label() for p in dia.samplePoints],
                numpoints=1, bbox_to_anchor = (0.91, 0.91))

    #Draw 2nd diagram
    ax2.plot_date(list(merged_full['date']), list(merged_full['ogimet_tmin']), '-', label='ogimet_tmin')
    ax2.scatter(list(merged_full['date']), list(merged_full['omsz_tmin']),
                label='omsz_tmin',
                marker=',',
                s=50,
                color='red')
    ax2.scatter(list(merged_full['date']), list(merged_full['idokep_tmin']),
                label='idokep_tmin',
                marker='*',
                s=50,
                color='blue')
    ax2.scatter(list(merged_full['date']), list(merged_full['koponyeg_tmin']),
                label='koponyeg_tmin',
                marker='^',
                s=50,
                color='orange')
    ax2.yaxis.set_major_locator(mticker.MaxNLocator(nbins=5, prune='lower'))
    ax2.grid(True)

    #Draw 3rd diagram
    ax3.plot_date(list(merged_full['date']), list(merged_full['ogimet_tmax']), '-', color='red', label='ogimet_tmax')
    ax3.scatter(list(merged_full['date']), list(merged_full['omsz_tmax']),
                label='omsz_tmax',
                marker=',',
                s=50,
                color='red')
    ax3.scatter(list(merged_full['date']), list(merged_full['idokep_tmax']),
                label='idokep_tmax',
                marker='*',
                s=50,
                color='blue')
    ax3.scatter(list(merged_full['date']), list(merged_full['koponyeg_tmax']),
                label='koponyeg_tmax',
                marker='^',
                s=50,
                color='orange')
    ax3.yaxis.set_major_locator(mticker.MaxNLocator(nbins=5, prune='lower'))
    ax3.grid(True)

    #Set figure size and save it
    fig.set_size_inches(20, 11.25) #1920x1080 pixel -> 20x11.25 inch
    fig.savefig('/home/pi/Desktop/1.png', facecolor=fig.get_facecolor())

graph_met()
"""
"""
    ax1_left.plot_date(list(merged_full['date']), list(merged_full['omsz_tmin']), '-', label='omsz_tmin')
    ax1_left.plot_date(list(merged_full['date']), list(merged_full['omsz_tmax']), '-', label='omsz_tmax')
    ax1_left.yaxis.set_major_locator(mticker.MaxNLocator(nbins=5, prune='lower'))

    ax2_left.plot_date(list(merged_full['date']), list(merged_full['idokep_tmin']), '-', label='idokep_tmin')
    ax2_left.plot_date(list(merged_full['date']), list(merged_full['idokep_tmax']), '-', label='idokep_tmax')
    ax2_left.yaxis.set_major_locator(mticker.MaxNLocator(nbins=5, prune='lower'))

    ax3_left.plot_date(list(merged_full['date']), list(merged_full['koponyeg_tmin']), '-', label='koponyeg_tmin')
    ax3_left.plot_date(list(merged_full['date']), list(merged_full['koponyeg_tmax']), '-', label='koponyeg_tmax')
    ax3_left.yaxis.set_major_locator(mticker.MaxNLocator(nbins=5, prune='lower'))

    ax1_right.bar(list(merged_full['date']),
                        list(merged_full['omsz_tmin']-merged_full['ogimet_tmin']), label='omsz_ogimet_min')
    #ax1_right.bar(list(merged_full['date']),
    #                    list(merged_full['omsz_tmax']-merged_full['ogimet_tmax']), label='omsz_ogimet_max')

    ax2_right.bar(list(merged_full['date']),
                  list(merged_full['idokep_tmin'] - merged_full['ogimet_tmin']), label='idokep_ogimet_min')
    #ax2_right.bar(list(merged_full['date']),
    #              list(merged_full['idokep_tmax'] - merged_full['ogimet_tmax']), label='omsz_ogimet_max')

    ax3_right.bar(list(merged_full['date']),
                  list(merged_full['koponyeg_tmin'] - merged_full['ogimet_tmin']), label='koponyeg_ogimet_min')
    #ax3_right.bar(list(merged_full['date']),
    #              list(merged_full['koponyeg_tmax'] - merged_full['ogimet_tmax']), label='koponyeg_ogimet_max')

    ax4.scatter(list(merged_full['date']), list(merged_full['ogimet_tmin']),
                label='ogimet_data_tmin',
                marker=',',
                s=50,
                color='blue')
    ax4.scatter(list(merged_full['date']), list(merged_full['ogimet_tmax']),
                label='ogimet_data_tmax',
                marker='.',
                s=100,
                color='red')

    ax4.plot_date(list(merged_full['date']),
                  [np.mean(x) for x in zip(merged_full['ogimet_tmin'], merged_full['ogimet_tmax'])],
                  '-',
                  label='ogimet_avg',
                  linewidth=2,
                  color='green')
    
    fig.set_size_inches(20, 11.25) #1920x1080 pixel -> 20x11.25 inch
    fig.savefig('/home/pi/Desktop/test.png', facecolor=fig.get_facecolor())
"""


"""
#Searching for absolute Tmin/Tmax values

ymin = min(x for x in omsz_vs_ogimet if x is not None)
ymax = max(x for x in omsz_vs_ogimet if x is not None)

if ymin < 0: ymin = ymin -1
elif ymin == 0: ymin = ymin - 1
elif ymin > 0: ymin = ymin + 1

if ymax < 0: ymax = ymax - 1
elif ymax == 0: ymax = ymax - 1
elif ymax > 0: ymax = ymax + 1


plt.ylim(ymin,ymax)
plt.legend()

plt.show()
"""
