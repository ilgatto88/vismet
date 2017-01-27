# -*- coding: utf-8 -*-

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import matplotlib.pyplot as plt
#from matplotlib import style
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from taylorDiagram import TaylorDiagram
import math
from scipy.interpolate import interp1d
from scipy.interpolate import pchip
from matplotlib.offsetbox import (TextArea, OffsetImage, AnchoredOffsetbox, AnnotationBbox)
from matplotlib.cbook import get_sample_data
import datetime

#General pyplot style can be used, but it makes problems with the Taylor-Diagram!
#style.use('fivethirtyeight')

desired_width = 640
pd.set_option('display.width', desired_width)

now_time = '{0:%Y-%m-%d}'.format(datetime.datetime.now())

#Start of the graphing function
def graph_met():

    #Define costumization settings (0: label, 1: marker, 2: color, 3: linestyle, 4: figsize, 5: alpha)
    cost_settings = dict(set1=[['OMSZ', '^', '#919191', '-', 10, 1.0],
                                ['Időkép', 'v', '#215edf', '-', 10, 0.9],
                                ['Köpönyeg', 'o', '#ea9f11', '-', 10, 0.7]])

    base_linewidth = 3
    grid_color = '#c2c4c2'
    grid_linestyle = '--'
    #print(cost_settings['set1'][0][5])
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.size"] = 13

    fig = plt.figure()
    fig.suptitle("Day1 Minimum & Maximum Temperature Forecast Verification: OMSZ / Időkép / Köpönyeg / vs. Observation\nBudapest", fontsize=18, weight='light')

    #Define diagram, subplots
    ax1_left = plt.subplot2grid((4, 10), (0, 0), rowspan=2, colspan=6)
    ax1_left.spines["top"].set_visible(False)
    ax1_left.spines["bottom"].set_visible(False)    
    ax1_left.spines["right"].set_visible(False)    
    ax1_left.spines["left"].set_visible(False)
    ax1_left.get_xaxis().tick_bottom()    
    ax1_left.get_yaxis().tick_left()
    #r'5-day moving $Tmin^{RMSE}$'
    plt.ylabel(s=r'5-day moving Avg($Tmin_{RMSE} + Tmax_{RMSE}$)')

    ax2 = plt.subplot2grid((4, 1), (2, 0), rowspan=1, colspan=1)
    ax2.spines["top"].set_visible(False)
    ax2.spines["bottom"].set_visible(False)    
    ax2.spines["right"].set_visible(False)    
    ax2.spines["left"].set_visible(False)
    ax2.get_xaxis().tick_bottom()    
    ax2.get_yaxis().tick_left()
    plt.ylabel('Tmax: Fcst vs. Obs [°C]')

    ax3 = plt.subplot2grid((4, 1), (3, 0), rowspan=1, colspan=1, sharex=ax2)
    ax3.spines["top"].set_visible(False)
    ax3.spines["bottom"].set_visible(False)    
    ax3.spines["right"].set_visible(False)    
    ax3.spines["left"].set_visible(False)
    ax3.get_xaxis().tick_bottom()    
    ax3.get_yaxis().tick_left()
    plt.ylabel('Tmin: Fcst vs. Obs [°C]')
	
    plt.subplots_adjust(left=0.05, bottom=0.05, right=0.95, top=0.95)#, wspace=0.2, hspace=0)

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
    sql_get_omsz = "SELECT fcst_date, fcst_tmin_for_day1, fcst_tmax_for_day1 FROM omsz_table ORDER BY timeofrequest DESC LIMIT 23;" #ORDER BY timeofrequest ASC
    cur.execute(sql_get_omsz)
    omsz_fetched = pd.DataFrame(cur.fetchall(), columns=['date', 'omsz_tmin', 'omsz_tmax'], dtype=int)

    sql_get_idokep = "SELECT fcst_tmin_for_day1, fcst_tmax_for_day1 FROM idokep_table ORDER BY timeofrequest DESC LIMIT 23;"
    cur.execute(sql_get_idokep)
    idokep_fetched = pd.DataFrame(cur.fetchall(), columns=['idokep_tmin', 'idokep_tmax'])

    sql_get_koponyeg = "SELECT fcst_tmin_for_day1, fcst_tmax_for_day1 FROM koponyeg_table ORDER BY timeofrequest DESC LIMIT 23;"
    cur.execute(sql_get_koponyeg)
    koponyeg_fetched = pd.DataFrame(cur.fetchall(), columns=['koponyeg_tmin', 'koponyeg_tmax'])

    sql_get_ogimet_tmin = "SELECT Tmin_date, Obs_Tmin FROM ogimet_table ORDER BY timeofrequest DESC LIMIT 23;"
    cur.execute(sql_get_ogimet_tmin)
    ogimet_fetched_uncorrected_tmin = pd.DataFrame(cur.fetchall(), columns=['date', 'ogimet_tmin'])

    sql_get_ogimet_tmax = "SELECT Tmax_date, Obs_Tmax FROM ogimet_table ORDER BY timeofrequest DESC LIMIT 23;"
    cur.execute(sql_get_ogimet_tmax)
    ogimet_fetched_uncorrected_tmax = pd.DataFrame(cur.fetchall(), columns=['date', 'ogimet_tmax'])


    #Putting provider data into a DataFrame
    frames_prov = [omsz_fetched, idokep_fetched, koponyeg_fetched]
    concat_prov = pd.concat(frames_prov, axis=1)

    merged_ogimet = pd.merge(ogimet_fetched_uncorrected_tmin, ogimet_fetched_uncorrected_tmax, on='date')
    merged_full_reverse = pd.merge(concat_prov, merged_ogimet)
    merged_full = merged_full_reverse[::-1]

    #Replacing nan to NA (string)
    #merged_full_NArepl_reverse = merged_full.replace(pd.np.nan, 'NA')
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


    ######Calculating 5 day moving RMSE of providers forecast vs observation######
    ###OMSZ Tmin & Tmax
    list4rmse_omsz = []
    
    for i in range(len(merged_full_NArepl[['date', 'omsz_tmin', 'omsz_tmax', 'ogimet_tmin', 'ogimet_tmax']])-5, -1, -1):
        l1_omsz_tmin = []
        l1_omsz_tmax = []
        for k in range(4, -1, -1):
            if merged_full_NArepl['omsz_tmin'][i+k] != 'NA' and merged_full_NArepl['ogimet_tmin'][i+k] != 'NA':
                l1_omsz_tmin.append((merged_full_NArepl['omsz_tmin'][i+k]-merged_full_NArepl['ogimet_tmin'][i+k])**2)
            else:
                l1_omsz_tmin.append(None)

            if merged_full_NArepl['omsz_tmax'][i+k] != 'NA' and merged_full_NArepl['ogimet_tmax'][i+k] != 'NA':
                l1_omsz_tmax.append((merged_full_NArepl['omsz_tmax'][i+k]-merged_full_NArepl['ogimet_tmax'][i+k])**2)
            else:
                l1_omsz_tmax.append(None)

        rmse_omsz_tmin = math.sqrt(sum(filter(lambda i: isinstance(i, float), l1_omsz_tmin))/5.0)
        rmse_omsz_tmax = math.sqrt(sum(filter(lambda i: isinstance(i, float), l1_omsz_tmax))/5.0)
        rmse_omsz_min_max = round((rmse_omsz_tmin + rmse_omsz_tmax) / 2.0, 2)
        list4rmse_omsz.append([merged_full_NArepl['date'][i].strftime("%B %d"), rmse_omsz_min_max])

    omsz_rmse5day_df = pd.DataFrame.from_records(list4rmse_omsz, columns=['date', 'rmse5day_omsz'])

    ######Calculating 5 day moving RMSE of providers forecast vs observation######
    ###Idokep Tmin & Tmax
    list4rmse_idokep = []
    for i in range(len(merged_full_NArepl[['date', 'omsz_tmin', 'omsz_tmax', 'ogimet_tmin', 'ogimet_tmax']])-5, -1, -1):
        l1_idokep_tmin = []
        l1_idokep_tmax = []
        for k in range(4, -1, -1):
            if merged_full_NArepl['idokep_tmin'][i+k] != 'NA' and merged_full_NArepl['ogimet_tmin'][i+k] != 'NA':
                l1_idokep_tmin.append((merged_full_NArepl['idokep_tmin'][i+k]-merged_full_NArepl['ogimet_tmin'][i+k])**2)
            else:
                l1_idokep_tmin.append(None)

            if merged_full_NArepl['idokep_tmax'][i+k] != 'NA' and merged_full_NArepl['ogimet_tmax'][i+k] != 'NA':
                l1_idokep_tmax.append((merged_full_NArepl['idokep_tmax'][i+k]-merged_full_NArepl['ogimet_tmax'][i+k])**2)
            else:
                l1_idokep_tmax.append(None)

        rmse_idokep_tmin = math.sqrt(sum(filter(lambda i: isinstance(i, float), l1_idokep_tmin))/5.0)
        rmse_idokep_tmax = math.sqrt(sum(filter(lambda i: isinstance(i, float), l1_idokep_tmax))/5.0)
        rmse_idokep_min_max = round((rmse_idokep_tmin + rmse_idokep_tmax) / 2.0, 2)
        list4rmse_idokep.append([merged_full_NArepl['date'][i].strftime("%B %d"), rmse_idokep_min_max])

    idokep_rmse5day_df = pd.DataFrame.from_records(list4rmse_idokep, columns=['date', 'rmse5day_idokep'])

    ######Calculating 5 day moving RMSE of providers forecast vs observation######
    ###koponyeg Tmin & Tmax
    list4rmse_koponyeg = []
    for i in range(len(merged_full_NArepl[['date', 'omsz_tmin', 'omsz_tmax', 'ogimet_tmin', 'ogimet_tmax']])-5, -1, -1):
        l1_koponyeg_tmin = []
        l1_koponyeg_tmax = []
        for k in range(4, -1, -1):
            if merged_full_NArepl['koponyeg_tmin'][i+k] != 'NA' and merged_full_NArepl['ogimet_tmin'][i+k] != 'NA':
                l1_koponyeg_tmin.append((merged_full_NArepl['koponyeg_tmin'][i+k]-merged_full_NArepl['ogimet_tmin'][i+k])**2)
            else:
                l1_koponyeg_tmin.append(None)

            if merged_full_NArepl['koponyeg_tmax'][i+k] != 'NA' and merged_full_NArepl['ogimet_tmax'][i+k] != 'NA':
                l1_koponyeg_tmax.append((merged_full_NArepl['koponyeg_tmax'][i+k]-merged_full_NArepl['ogimet_tmax'][i+k])**2)
            else:
                l1_koponyeg_tmax.append(None)

        rmse_koponyeg_tmin = math.sqrt(sum(filter(lambda i: isinstance(i, float), l1_koponyeg_tmin))/5.0)
        rmse_koponyeg_tmax = math.sqrt(sum(filter(lambda i: isinstance(i, float), l1_koponyeg_tmax))/5.0)
        rmse_koponyeg_min_max = round((rmse_koponyeg_tmin + rmse_koponyeg_tmax) / 2.0, 2)
        list4rmse_koponyeg.append([merged_full_NArepl['date'][i].strftime("%B %d"), rmse_koponyeg_min_max])

    koponyeg_rmse5day_df = pd.DataFrame.from_records(list4rmse_koponyeg, columns=['date', 'rmse5day_koponyeg'])

    #Merging providers rmse dataframes
    providers_rmse5day_df_omsz_idokep = omsz_rmse5day_df.merge(idokep_rmse5day_df, how='inner', on='date')
    providers_rmse5day_df = providers_rmse5day_df_omsz_idokep.merge(koponyeg_rmse5day_df, how='inner', on='date')
    providers_rmse5day_df.columns = ['date', 'rmse5day_omsz', 'rmse5day_idokep', 'rmse5day_koponyeg']

    #Draw 1st diagram
    base_daterange = range(0, len(providers_rmse5day_df['date']))
    omsz_rmse_y = list(providers_rmse5day_df['rmse5day_omsz'])
    idokep_rmse_y = list(providers_rmse5day_df['rmse5day_idokep'])#[::-1]
    koponyeg_rmse_y = list(providers_rmse5day_df['rmse5day_koponyeg'])
    interp_daterange = np.linspace(0, len(providers_rmse5day_df['date']), len(providers_rmse5day_df['date'])*10)

    interp_omsz = pchip(base_daterange, omsz_rmse_y)
    interp_idokep = pchip(base_daterange, idokep_rmse_y)
    interp_koponyeg = pchip(base_daterange, koponyeg_rmse_y)


    
    ax1_left.plot(interp_daterange[:-10], interp_omsz(interp_daterange)[:-10], cost_settings['set1'][0][3],
        label='rmse5day_omsz',
        linewidth=base_linewidth,
        color=cost_settings['set1'][0][2])

    #print(interp_daterange[:-10])
    #print(interp_omsz(interp_daterange)[:-10])

    ax1_left.plot(base_daterange, omsz_rmse_y, ' ',
                label='rmse5day_omsz_dots',
                marker=cost_settings['set1'][0][1],
                mec='black',
                ms=cost_settings['set1'][0][4],
                alpha=cost_settings['set1'][0][5],
                color=cost_settings['set1'][0][2],
                clip_on = False)

    ax1_left.plot(interp_daterange[:-10], interp_idokep(interp_daterange)[:-10],
        cost_settings['set1'][1][3],
        label='rmse5day_idokep',
        linewidth=base_linewidth,
        color=cost_settings['set1'][1][2])

    ax1_left.plot(base_daterange, idokep_rmse_y, ' ',
                label='idokep_tmax',
                marker=cost_settings['set1'][1][1],
                mec='black',
                ms=cost_settings['set1'][0][4],
                alpha=cost_settings['set1'][1][5],
                color=cost_settings['set1'][1][2],
                clip_on = False)

    ax1_left.plot(interp_daterange[:-10], interp_koponyeg(interp_daterange)[:-10],
        cost_settings['set1'][2][3],
        label='rmse5day_koponyeg',
        linewidth=base_linewidth,
        color=cost_settings['set1'][2][2])

    ax1_left.plot(base_daterange, koponyeg_rmse_y, ' ',
                label='koponyeg_tmax',
                marker=cost_settings['set1'][2][1],
                mec='black',
                ms=cost_settings['set1'][0][4],
                alpha=cost_settings['set1'][2][5],
                color=cost_settings['set1'][2][2],
                clip_on = False)
    
    ax1_left.set_xticklabels(list(providers_rmse5day_df['date'])[::4])
    ax1_left.xaxis.set_major_locator(mticker.MaxNLocator(nbins=5))
    ax1_left.yaxis.set_label_coords(-0.05, 0.5)

    ax1_left.tick_params(axis='x',     # changes apply to the x-axis
                    which='both',      # both major and minor ticks are affected
                    bottom='off',      # ticks along the bottom edge are off
                    top='off',         # ticks along the top edge are off
                    labelbottom='on') # labels along the bottom edge are on

    ax1_left.yaxis.set_major_locator(mticker.MaxNLocator(nbins=5, prune='lower'))
    
    
    #Searching for absolute Tmin/Tmax values
    #Ymin
    rmse_mins = [ float(providers_rmse5day_df['rmse5day_omsz'].min()),
                    float(providers_rmse5day_df['rmse5day_idokep'].min()),
                    float(providers_rmse5day_df['rmse5day_koponyeg'].min()) ]
    ymin_diag1 = math.floor(min(rmse_mins))
    #Ymax
    rmse_maxs = [ float(providers_rmse5day_df['rmse5day_omsz'].max()),
                    float(providers_rmse5day_df['rmse5day_idokep'].max()),
                    float(providers_rmse5day_df['rmse5day_koponyeg'].max()) ]
    ymax_diag1 = math.ceil(max(rmse_maxs))

    if abs(ymin_diag1 - min(rmse_mins)) < 0.2: ymin_diag1 -= 1
    if abs(ymax_diag1 - max(rmse_maxs)) < 0.2: ymax_diag1 += 1
    ax1_left.set_ylim([ymin_diag1,ymax_diag1])
    
    bbox_props = dict(boxstyle='round', fc='white', ec='#ebebe0')
    
    omsz_ydiff = 0
    idokep_ydiff = 0
    koponyeg_ydiff = 0

    omsz_rmse_lastval = providers_rmse5day_df['rmse5day_omsz'][len(providers_rmse5day_df['rmse5day_omsz'])-1]
    idokep_rmse_lastval = providers_rmse5day_df['rmse5day_idokep'][len(providers_rmse5day_df['rmse5day_idokep'])-1]
    koponyeg_rmse_lastval = providers_rmse5day_df['rmse5day_koponyeg'][len(providers_rmse5day_df['rmse5day_koponyeg'])-1]

    if omsz_rmse_lastval >= idokep_rmse_lastval and omsz_rmse_lastval >= koponyeg_rmse_lastval:
        if idokep_rmse_lastval >= koponyeg_rmse_lastval:
            if abs(omsz_rmse_lastval - idokep_rmse_lastval) < 0.2:
                omsz_ydiff += 0.2
            if abs(idokep_rmse_lastval - koponyeg_rmse_lastval) < 0.2:
                koponyeg_ydiff -= 0.2
        else:
            if abs(omsz_rmse_lastval - koponyeg_rmse_lastval) < 0.2:
                omsz_ydiff += 0.2
            if abs(koponyeg_rmse_lastval - idokep_rmse_lastval) < 0.2:
                idokep_ydiff -= 0.2

    elif idokep_rmse_lastval >= omsz_rmse_lastval and idokep_rmse_lastval >= koponyeg_rmse_lastval:
        if omsz_rmse_lastval >= koponyeg_rmse_lastval:
            if abs(idokep_rmse_lastval - omsz_rmse_lastval) < 0.2:
                idokep_ydiff += 0.2
            if abs(omsz_rmse_lastval - koponyeg_rmse_lastval) < 0.2:
                koponyeg_ydiff -= 0.2
        else:
            if abs(idokep_rmse_lastval - koponyeg_rmse_lastval) < 0.2:
                idokep_ydiff += 0.2
            if abs(koponyeg_rmse_lastval - omsz_rmse_lastval) < 0.2:
                omsz_ydiff -= 0.2

    elif koponyeg_rmse_lastval >= omsz_rmse_lastval and koponyeg_rmse_lastval >= koponyeg_rmse_lastval:
        if omsz_rmse_lastval >= idokep_rmse_lastval:
            if abs(koponyeg_rmse_lastval - omsz_rmse_lastval) < 0.2:
                koponyeg_ydiff += 0.2
            if abs(omsz_rmse_lastval - idokep_rmse_lastval) < 0.2:
                idokep_ydiff -= 0.2
        else:
            if abs(koponyeg_rmse_lastval - idokep_rmse_lastval) < 0.2:
                koponyeg_ydiff += 0.2
            if abs(idokep_rmse_lastval - omsz_rmse_lastval) < 0.2:
                omsz_ydiff -= 0.2

    if omsz_ydiff != 0 or idokep_ydiff != 0 or koponyeg_ydiff != 0:
        print('Adjusted the annotations.')
        if omsz_ydiff != 0:
            print('OMSZ annotation y position changed:', omsz_ydiff)
        if idokep_ydiff != 0:
            print('Idokep annotation y position changed:', idokep_ydiff)
        if koponyeg_ydiff != 0:
            print('Koponyeg annotation y position changed:', koponyeg_ydiff)
    
    ax1_left.annotate('\u25b2' + ': ' + str(round(omsz_rmse_lastval, 2)),  # Value of annotation
                        (16.0, omsz_rmse_lastval),
                        bbox=bbox_props,
                        color=cost_settings['set1'][0][2],
                        size=8,
                        xytext = (16.3, omsz_rmse_lastval + omsz_ydiff))
    
    ax1_left.annotate('\u25bc' + ': ' + str(round(idokep_rmse_lastval, 1)),  # Value of annotation
                        (16.0, idokep_rmse_lastval),
                        bbox=bbox_props,
                        color=cost_settings['set1'][1][2],
                        size=8,
                        xytext = (16.3, idokep_rmse_lastval + idokep_ydiff))

    ax1_left.annotate('\u25cf' + ': ' + str(round(koponyeg_rmse_lastval, 1)),  # Value of annotation
                        (16.0, koponyeg_rmse_lastval),
                        bbox=bbox_props,
                        color=cost_settings['set1'][2][2],
                        size=8,
                        xytext = (16.3, koponyeg_rmse_lastval + koponyeg_ydiff))
    
    ax1_left.set_position([0.05, 0.5, 0.52, 0.4])
    ax1_left.grid(True, linestyle=grid_linestyle, color=grid_color)
    

    #######################################################
    ###################Taylor-diagram######################
    #Defining sample data (providers stdev, corr and name)

    samples = dict(alap=[[np.std(merged_full['omsz_tmin']+merged_full['omsz_tmax']),
                            round(df_for_corr_omsz.corr()['OMSZ'][1], 4), cost_settings['set1'][0][0], cost_settings['set1'][0][1], cost_settings['set1'][0][2]],
                         [np.std(merged_full['idokep_tmin'] + merged_full['idokep_tmax']),
                            round(df_for_corr_idokep.corr()['Idokep'][1], 4), cost_settings['set1'][1][0], cost_settings['set1'][1][1], cost_settings['set1'][1][2]],
                         [np.std(merged_full['koponyeg_tmin'] + merged_full['koponyeg_tmax']),
                            round(df_for_corr_koponyeg.corr()['Koponyeg'][1], 4), cost_settings['set1'][2][0], cost_settings['set1'][2][1], cost_settings['set1'][2][2]]])

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
    for i,(stddev, corrcoef, name, marker1, colors1) in enumerate(samples['alap']):
        dia.add_sample(stddev, corrcoef,
                       marker=marker1, ms=10, ls='', # marker='$%d$' % (i+1)
                       mfc=colors1, mec='black', # Colors
                       #mfc=colors[i], mec=colors[i], # Colors
                       label=name)


    #Adjust contours, labels and legend
    contours = dia.add_contours(levels=5, colors='0.5') # levels: number of stdev inner circles, colors: 0=white 1=black 0.5=~grey
    dia.ax.clabel(contours, inline=1, fontsize=10, fmt='%.1f') # inline: 1/0 curved line is cut under the numbers, fmt(format)

    #Legend settings
    fig.legend(dia.samplePoints,
               [p.get_label() for p in dia.samplePoints],
                numpoints=1, bbox_to_anchor = (0.96, 0.90))

    dia._ax.set_position([0.54, 0.49, 0.40, 0.40])
                
    ############################
    ######Draw 2nd diagram######
    ############################
    base_daterange_diag2 = range(0, len(merged_full['date']))
    ogimet_diag2_y = list(merged_full['ogimet_tmax'])
    omsz_diag2_y = list(merged_full['omsz_tmax'])
    idokep_diag2_y = list(merged_full['idokep_tmax'])
    koponyeg_diag2_y = list(merged_full['koponyeg_tmax'])
    interp_daterange_diag2 = np.linspace(0, len(merged_full['date']), len(merged_full['date'])*10)

    interp = pchip(base_daterange_diag2, ogimet_diag2_y)
    
    ax2.plot(interp_daterange_diag2[:-10], interp(interp_daterange_diag2)[:-10], '-', label='ogimet_tmax', linewidth=base_linewidth, color='black')
    
    ax2.plot(base_daterange_diag2, omsz_diag2_y, ' ',
                label='omsz_tmax',
                marker=cost_settings['set1'][0][1],
                mec='black',
                ms=cost_settings['set1'][0][4],
                alpha=cost_settings['set1'][0][5],
                color=cost_settings['set1'][0][2],
                clip_on = False)

    ax2.plot(base_daterange_diag2, idokep_diag2_y, ' ',
                label='idokep_tmax',
                marker=cost_settings['set1'][1][1],
                mec='black',
                ms=cost_settings['set1'][0][4],
                alpha=cost_settings['set1'][1][5],
                color=cost_settings['set1'][1][2],
                clip_on = False)

    ax2.plot(base_daterange_diag2, koponyeg_diag2_y, ' ',
                label='koponyeg_tmax',
                marker=cost_settings['set1'][2][1],
                mec='black',
                ms=cost_settings['set1'][0][4],
                alpha=cost_settings['set1'][2][5],
                color=cost_settings['set1'][2][2],
                clip_on = False)

    ax2.yaxis.set_major_locator(mticker.MaxNLocator(nbins=4, prune='lower'))
    ax2.yaxis.set_label_coords(-0.03, 0.5)
    plt.setp(ax2.get_xticklabels(), visible=False)
    
    #Searching for absolute Tmin/Tmax values, diag3
    #Ymin
    mins_diag2 = [ float(merged_full['ogimet_tmax'].min()),
                    float(merged_full['omsz_tmax'].min()),
                    float(merged_full['idokep_tmax'].min()),
                    float(merged_full['koponyeg_tmax'].min()) ]
    ymin_diag2 = math.floor(min(mins_diag2))
    #Ymax
    maxs_diag2 = [ float(merged_full['ogimet_tmax'].max()),
                    float(merged_full['omsz_tmax'].max()),
                    float(merged_full['idokep_tmax'].max()),
                    float(merged_full['koponyeg_tmax'].max()) ]
    ymax_diag2 = math.ceil(max(maxs_diag2))
    
    if abs(ymin_diag2 - min(mins_diag2)) < 1: ymin_diag2 -= 1
    if abs(ymax_diag2 - max(maxs_diag2)) < 1: ymax_diag2 += 1
    ax2.set_ylim([ymin_diag2,ymax_diag2])

    ax2.tick_params(axis='x',     # changes apply to the x-axis
                    which='both',      # both major and minor ticks are affected
                    bottom='off',      # ticks along the bottom edge are off
                    top='off',         # ticks along the top edge are off
                    labelbottom='on') # labels along the bottom edge are on

    ax2.set_position([0.05, 0.27, 0.9, 0.16])
    ax2.grid(True, linestyle=grid_linestyle, color=grid_color)
    
    #Draw 3rd diagram
    base_daterange_diag3 = range(0, len(merged_full['date']))
    ogimet_diag3_y = list(merged_full['ogimet_tmin'])
    ogimet_diag3_y = list(merged_full['ogimet_tmin'])
    omsz_diag3_y = list(merged_full['omsz_tmin'])
    idokep_diag3_y = list(merged_full['idokep_tmin'])
    koponyeg_diag3_y = list(merged_full['koponyeg_tmin'])
    interp_daterange_diag3 = np.linspace(0, len(merged_full['date']), len(merged_full['date'])*10)

    interp = pchip(base_daterange_diag3, ogimet_diag3_y)
    
    ax3.plot(interp_daterange_diag3[:-10], interp(interp_daterange_diag3)[:-10], '-', label='ogimet_tmin', linewidth=base_linewidth, color='black')
    
    ax3.plot(base_daterange_diag3, omsz_diag3_y, ' ',
                label='omsz_tmin',
                marker=cost_settings['set1'][0][1],
                mec='black',
                ms=cost_settings['set1'][0][4],
                alpha=cost_settings['set1'][0][5],
                color=cost_settings['set1'][0][2],
                clip_on = False)

    ax3.plot(base_daterange_diag3, idokep_diag3_y, ' ',
                label='idokep_tmin',
                marker=cost_settings['set1'][1][1],
                mec='black',
                ms=cost_settings['set1'][0][4],
                alpha=cost_settings['set1'][1][5],
                color=cost_settings['set1'][1][2],
                clip_on = False)

    ax3.plot(base_daterange_diag3, koponyeg_diag3_y, ' ',
                label='koponyeg_tmin',
                marker=cost_settings['set1'][2][1],
                mec='black',
                ms=cost_settings['set1'][0][4],
                alpha=cost_settings['set1'][2][5],
                color=cost_settings['set1'][2][2],
                clip_on = False)

    ax3.yaxis.set_major_locator(mticker.MaxNLocator(nbins=4, prune='upper'))
    ax3.xaxis.set_major_locator(mticker.MaxNLocator(nbins=5))
    ax3.yaxis.set_label_coords(-0.03, 0.5)
    list_newDateFormat = []
    for i in range(len(merged_full['date'])):
        list_newDateFormat.append(merged_full['date'][i].strftime("%B %d"))

    ax3.tick_params(axis='x',     # changes apply to the x-axis
                    which='both',      # both major and minor ticks are affected
                    bottom='off',      # ticks along the bottom edge are off
                    top='off',         # ticks along the top edge are off
                    labelbottom='on') # labels along the bottom edge are on


    ax3.set_xticklabels(list_newDateFormat[::-4])
    #ax3.set_xticklabels(list(providers_rmse5day_df['date'])[::2])
    #ax3.xaxis.set_major_formatter(mdates.DateFormatter('%B %d'))

    
    #Searching for absolute Tmin/tmax values, diag3
    #Ymin
    mins_diag3 = [ float(merged_full['ogimet_tmin'].min()),
                    float(merged_full['omsz_tmin'].min()),
                    float(merged_full['idokep_tmin'].min()),
                    float(merged_full['koponyeg_tmin'].min()) ]
    ymin_diag3 = math.floor(min(mins_diag3))
    #Ymax
    maxs_diag3 = [ float(merged_full['ogimet_tmin'].max()),
                    float(merged_full['omsz_tmin'].max()),
                    float(merged_full['idokep_tmin'].max()),
                    float(merged_full['koponyeg_tmin'].max()) ]
    ymax_diag3 = math.ceil(max(maxs_diag3))
    
    if abs(ymin_diag3 - min(mins_diag3)) < 1: ymin_diag3 -= 1
    if abs(ymax_diag3 - max(maxs_diag3)) < 1: ymax_diag3 += 1
    ax3.set_ylim([ymin_diag3,ymax_diag3])
    ax3.grid(True, linestyle=grid_linestyle, color=grid_color)

    #Adding Python logo to the lower right corner
    python_logo = get_sample_data('/home/pi/learning_python/vismet/python.png', asfileobj=False)
    arr_img = plt.imread(python_logo, format='png')
    imagebox = OffsetImage(arr_img, zoom=0.50, alpha=0.20)
    imagebox.image.axes = ax3

    ax3.add_artist(AnnotationBbox(imagebox, [10.0, 0.0],
                                xybox=(670., -110.),
                                pad=0,
                                frameon=False,
                                boxcoords="offset points"))

    ax3.annotate(str(now_time)+' @ János Tordai', xy=(0.9, -0.06), xytext=(12, -12), va='top',
             xycoords='axes fraction', textcoords='offset points', alpha=0.25, color='black')
    
    ax3.set_position([0.05, 0.05, 0.9, 0.16])
    #Set figure size and save it
    fig.set_size_inches(20, 11.25) #1920x1080 pixel -> 20x11.25 inch
    fig.savefig('/home/pi/Desktop/vismet_day1_'+str(now_time)+'.png', facecolor='white')#fig.get_facecolor())

graph_met()