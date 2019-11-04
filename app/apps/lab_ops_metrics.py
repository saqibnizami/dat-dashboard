import calendar
import os
import time
import urllib.parse
from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output, State
from dateutil import relativedelta
from sklearn.linear_model import LinearRegression

from app import app, logger

os.environ['TZ'] = 'America/Los_Angeles'
pd.options.mode.chained_assignment = None  # default='warn'


#app stuff
description = 'Key operations metrics for samples & reports'

class LabOpsDAO:

    @staticmethod
    def get_orders():
        try:
            # orders created (jon query)
            df_orders = pd.read_csv('~/data_pulls/lab_ops_metrics/orders_data.csv')
            df_orders['order_created_at'] = df_orders['order_created_at'].astype(dtype='datetime64[ns]')
            df_orders['order_created_at'] = df_orders['order_created_at'].apply(lambda x: x.replace(tzinfo=None))
            return df_orders
        except Exception as e:
            logger.exception('')

    @staticmethod
    def get_kits():
        try:
            # kits shipped (engineering query)
            df_kits = pd.read_csv('~/data_pulls/lab_ops_metrics/kits_data.csv')
            df_kits['ship_date'] = df_kits['ship_date'].astype(dtype='datetime64[ns]')
            df_kits['ship_date'] = df_kits['ship_date'].apply(lambda x: x.replace(tzinfo=None))
            return df_kits
        except Exception as e:
            logger.exception('')

    @staticmethod
    def get_samples():
        try:
            # samples accessioned (erica query)
            df_samples = pd.read_csv('~/data_pulls/lab_ops_metrics/samples_data.csv')
            df_samples['sample_received'] = df_samples['sample_received'].astype(dtype='datetime64[ns]')
            df_samples['sample_received'] = df_samples['sample_received'].apply(lambda x: x.replace(tzinfo=None))
            return df_samples
        except Exception as e:
            logger.exception('')

    @staticmethod
    def get_blocked_reports():
        try:
            # reports blocked
            df_blocked = pd.read_csv('~/data_pulls/lab_ops_metrics/reports_blocked_data.csv')
            df_blocked['sample_received'] = df_blocked['sample_received'].astype(dtype='datetime64[ns]')
            df_blocked['sample_received'] = df_blocked['sample_received'].apply(lambda x: x.replace(tzinfo=None))

            df_orders_kits = pd.merge(LabOpsDAO.get_orders(), LabOpsDAO.get_kits(), on='delivery_id', how='left')
            df_orders_kits = df_orders_kits.sort_values(by=['order_id', 'ship_date'], ascending=True).drop_duplicates(
                subset='order_id', keep='first', inplace=False)

            df_blocked = pd.merge(df_orders_kits, df_blocked, on='sample_id', how='right')
            return df_blocked
        except Exception as e:
            logger.exception('')

    @staticmethod
    def get_released_reports():
        try:
            # reports released (erica query)
            df_reports = pd.read_csv('~/data_pulls/lab_ops_metrics/reports_released_data.csv')
            df_reports['report_created_at'] = df_reports['report_created_at'].astype(dtype='datetime64[ns]')
            df_reports['report_created_at'].apply(lambda x: datetime.replace(x, tzinfo=None))
            return df_reports
        except Exception as e:
            logger.exception('')

    @staticmethod
    def get_report_corrections():
        try:
            # report corrections
            df_results = pd.read_csv('~/data_pulls/lab_ops_metrics/report_corrections_data.csv')
            df_results['result_created_at'] = df_results['result_created_at'].astype(dtype='datetime64[ns]')
            df_results['result_created_at'] = df_results['result_created_at'].apply(lambda x: x.replace(tzinfo=None))
            return df_results
        except Exception as e:
            logger.exception('')

    @staticmethod
    def get_tat():
        try:
            # Turn around time
            df_tat = pd.read_csv('~/data_pulls/lab_ops_metrics/results_tat_data.csv')
            return df_tat
        except Exception as e:
            logger.exception('')

    @staticmethod
    def get_issue_types():
        try:
            df_issue_types = pd.read_csv('app/data/static/issue_types.csv')
            return df_issue_types
        except Exception as e:
            logger.exception('')

    @staticmethod
    def get_blocked_reports_with_issue_type():
        df_blocked = LabOpsDAO.get_blocked_reports()
        issue_types = LabOpsDAO.get_issue_types()

        df_blocked = df_blocked[df_blocked.order_id.notnull()]
        df_blocked = df_blocked[~df_blocked['state'].isin(
            ['RELEASED', 'CANCELLED', 'CANCELLED_BY_PATIENT', 'REJECTED_BY_UBIOME', 'RECOLLECTED'])]

        merged_blocked = pd.merge(df_blocked, issue_types, on='issue_id', how='left')
        return merged_blocked


def month_dates():
    current_year = datetime.now().year
    current_month = datetime.now().month
    if (current_month == 1):
        previous_year = current_year - 1
        previous_month = 12
    else:
        previous_year = current_year
        previous_month = current_month - 1

    #current month
    days_in_current_month = calendar.monthrange(current_year, current_month)[1]
    first_day_current_month = datetime(current_year, current_month, 1)
    last_day_current_month = datetime(current_year, current_month, calendar.monthrange(current_year, current_month)[1])

    #previous month
    days_in_previous_month = calendar.monthrange(previous_year, previous_month)
    first_day_previous_month = datetime(previous_year, previous_month, 1)
    last_day_previous_month = datetime(previous_year, previous_month, calendar.monthrange(previous_year, previous_month)[1])

    return first_day_current_month, last_day_current_month, first_day_previous_month, last_day_previous_month

#data manip functions
def data_for_sample_accessioned_mtd_chart(product):
    df_samples = LabOpsDAO.get_samples()

    #identify current and previous month start and end dates
    first_day_current_month, last_day_current_month, first_day_previous_month, last_day_previous_month = month_dates()

    #Product Filter
    try:
        if product == 'smartgut':
            df_samples = df_samples[df_samples['kit_type'] == 16]
        elif product == 'smartjane':
            df_samples = df_samples[df_samples['kit_type'] == 17]
    except:
        return pd.DataFrame()

    df_samples_accessioned = df_samples

    #previous month
    df_samples_accessioned_previous_month = df_samples_accessioned[(df_samples_accessioned['sample_received'] >= first_day_previous_month) & (df_samples_accessioned['sample_received'] < last_day_previous_month + timedelta(days=1))]
    df_samples_accessioned_previous_month.index = df_samples_accessioned_previous_month['sample_received']
    df_samples_accessioned_previous_month_daily = df_samples_accessioned_previous_month.resample('D').sample_id.nunique()
    df_samples_accessioned_previous_month_daily.index = df_samples_accessioned_previous_month_daily.index.day
    df_samples_accessioned_previous_month = df_samples_accessioned_previous_month_daily.cumsum()

    #current month
    df_samples_accessioned_current_month = df_samples_accessioned[(df_samples_accessioned['sample_received'] >= first_day_current_month) & (df_samples_accessioned['sample_received'] < last_day_current_month + timedelta(days=1))]
    df_samples_accessioned_current_month.index = df_samples_accessioned_current_month['sample_received']
    df_samples_accessioned_current_month_daily = df_samples_accessioned_current_month.resample('D').sample_id.nunique()
    df_samples_accessioned_current_month_daily.index = df_samples_accessioned_current_month_daily.index.day
    while (len(df_samples_accessioned_current_month_daily) < datetime.now().day):
        df_samples_accessioned_current_month_daily = df_samples_accessioned_current_month_daily.append(pd.Series([0]), ignore_index=True)
    df_samples_accessioned_current_month = df_samples_accessioned_current_month_daily.cumsum()
    #catch exception for first day of month
    try:
        if min(df_samples_accessioned_current_month.index) < 1:
            df_samples_accessioned_current_month.index += 1
        if min(df_samples_accessioned_current_month_daily.index) < 1:
            df_samples_accessioned_current_month_daily.index += 1
    except:
        pass

    #combine previous and current into same dataframe
    df_samples_accessioned_mtd = pd.concat([df_samples_accessioned_previous_month, df_samples_accessioned_current_month, df_samples_accessioned_current_month_daily, df_samples_accessioned_previous_month_daily], axis=1)
    df_samples_accessioned_mtd.columns = [['previous_month_count', 'current_month_count', 'current_month_daily', 'previous_month_daily']]
    df_samples_accessioned_mtd['previous_month_count'] = df_samples_accessioned_mtd['previous_month_count'].fillna(0)
    df_samples_accessioned_mtd['previous_month_daily'] = df_samples_accessioned_mtd['previous_month_daily'].fillna(0)

    #linreg trendline
    #catch exception for first day of month
    try:
        if len(df_samples_accessioned_mtd['current_month_count'] >= 2):
            linear_regressor = LinearRegression()
            linear_regressor.fit(df_samples_accessioned_mtd['current_month_count'].dropna().index.values.reshape(-1, 1), df_samples_accessioned_mtd['current_month_count'].dropna().unstack().values.reshape(-1,1))
            Y_pred = linear_regressor.predict(df_samples_accessioned_mtd['current_month_count'].index[:last_day_current_month.day].values.reshape(-1,1))
            predicted_values = pd.Series(Y_pred.flatten()).round(0)
            predicted_values.index = predicted_values.index + 1
            predicted_values = predicted_values[df_samples_accessioned_mtd[df_samples_accessioned_mtd['current_month_count'].isnull().any(axis=1)].index[0] - 1:]
            df_samples_accessioned_mtd['predicted_count'] = predicted_values
        else: df_samples_accessioned_mtd['predicted_count'] = ''
    except:
        df_samples_accessioned_mtd['predicted_count'] = ''

    return df_samples_accessioned_mtd

def data_for_sample_processed_successfully_mtd_chart(product):
    df_orders = LabOpsDAO.get_orders()
    df_samples = LabOpsDAO.get_samples()
    df_results = LabOpsDAO.get_report_corrections()

    #identify current and previous month start and end dates
    first_day_current_month, last_day_current_month, first_day_previous_month, last_day_previous_month = month_dates()

    #Product Filter
    try:
        if product == 'smartgut':
            df_orders = df_orders[df_orders['code'] == 'smart_gut']
            df_samples = df_samples[df_samples['kit_type'] == 16]
            #df results is never used solo, so it is filtered on merges
        elif product == 'smartjane':
            df_orders = df_orders[df_orders['code'] == 'smart_jane']
            df_samples = df_samples[df_samples['kit_type'] == 17]
            #df results is never used solo, so it is filtered on merges
    except:
        return pd.DataFrame()

    #GOAL 2: SAMPLES PROCESSED SUCCESSFULLY MONTH TO DATE
    df_orders_samples = pd.merge(df_orders, df_samples, how='inner', on='sample_id')
    df_orders_samples_results = pd.merge(df_orders_samples, df_results, how='inner', on='order_id')
    df_orders_samples_results_process_success = df_orders_samples_results[df_orders_samples_results['sample_process_status'] == 'success']
    df_orders_samples_results_process_success = df_orders_samples_results_process_success.sort_values(by=['order_id', 'result_created_at'], ascending=True).drop_duplicates(subset=['order_id'], keep='first')

    df_orders_samples_results_process_success_current_month = df_orders_samples_results_process_success[(df_orders_samples_results_process_success['result_created_at'] >= first_day_current_month) & (df_orders_samples_results_process_success['result_created_at'] < last_day_current_month + timedelta(days=1))]
    df_orders_samples_results_process_success_current_month.index = df_orders_samples_results_process_success_current_month['result_created_at']
    df_orders_samples_results_process_success_current_month_daily = df_orders_samples_results_process_success_current_month.resample('D').order_id.nunique()
    df_orders_samples_results_process_success_current_month_daily.index = df_orders_samples_results_process_success_current_month_daily.index.day
    while (len(df_orders_samples_results_process_success_current_month_daily) < datetime.now().day):
        df_orders_samples_results_process_success_current_month_daily = df_orders_samples_results_process_success_current_month_daily.append(pd.Series([0]), ignore_index=True)
    df_orders_samples_results_process_success_current_month = df_orders_samples_results_process_success_current_month_daily.cumsum()
    #catch exception for first day of month
    try:
        if min(df_orders_samples_results_process_success_current_month.index) < 1:
            df_orders_samples_results_process_success_current_month.index += 1
        if min(df_orders_samples_results_process_success_current_month_daily.index) < 1:
            df_orders_samples_results_process_success_current_month_daily.index += 1
    except: pass

    df_orders_samples_results_process_success_previous_month = df_orders_samples_results_process_success[(df_orders_samples_results_process_success['result_created_at'] >= first_day_previous_month) & (df_orders_samples_results_process_success['result_created_at'] < last_day_previous_month + timedelta(days=1))]
    df_orders_samples_results_process_success_previous_month.index = df_orders_samples_results_process_success_previous_month['result_created_at']
    df_orders_samples_results_process_success_previous_month_daily = df_orders_samples_results_process_success_previous_month.resample('D').order_id.nunique()
    df_orders_samples_results_process_success_previous_month_daily.index = df_orders_samples_results_process_success_previous_month_daily.index.day
    df_orders_samples_results_process_success_previous_month.index = df_orders_samples_results_process_success_previous_month.index.day
    df_orders_samples_results_process_success_previous_month = df_orders_samples_results_process_success_previous_month_daily.cumsum()

    #combine previous and current into same dataframe
    df_orders_samples_results_process_success_mtd = pd.concat([df_orders_samples_results_process_success_previous_month, df_orders_samples_results_process_success_current_month, df_orders_samples_results_process_success_current_month_daily, df_orders_samples_results_process_success_previous_month_daily], axis=1)
    df_orders_samples_results_process_success_mtd.columns = [['previous_month_count', 'current_month_count', 'current_month_daily', 'previous_month_daily']]
    df_orders_samples_results_process_success_mtd['previous_month_count'] = df_orders_samples_results_process_success_mtd['previous_month_count'].fillna(0)
    df_orders_samples_results_process_success_mtd['previous_month_daily'] = df_orders_samples_results_process_success_mtd['previous_month_daily'].fillna(0)

    #linreg trendline
    #catch exception for first day of month
    try:
        linear_regressor = LinearRegression()
        linear_regressor.fit(df_orders_samples_results_process_success_mtd['current_month_count'].dropna().index.values.reshape(-1, 1), df_orders_samples_results_process_success_mtd['current_month_count'].dropna().unstack().values.reshape(-1,1))
        Y_pred = linear_regressor.predict(df_orders_samples_results_process_success_mtd['current_month_count'].index[:last_day_current_month.day].values.reshape(-1,1))
        predicted_values = pd.Series(Y_pred.flatten()).round(0)
        predicted_values.index = predicted_values.index + 1
        predicted_values = predicted_values[df_orders_samples_results_process_success_mtd[df_orders_samples_results_process_success_mtd['current_month_count'].isnull().any(axis=1)].index[0] - 1:]
        df_orders_samples_results_process_success_mtd['predicted_count'] = predicted_values
    except: df_orders_samples_results_process_success_mtd['predicted_count'] = ''

    return df_orders_samples_results_process_success_mtd

def data_for_reports_released_mtd_chart(product):
    df_reports = LabOpsDAO.get_released_reports()
    #identify current and previous month start and end dates
    first_day_current_month, last_day_current_month, first_day_previous_month, last_day_previous_month = month_dates()

    #Product Filter
    try:
        if product == 'smartgut':
            df_reports = df_reports[df_reports['order_type_id'] == 'd93422aa-b3e7-4077-af20-61d560f73880']
        elif product == 'smartjane':
            df_reports = df_reports[df_reports['order_type_id'] == 'fbc0caae-725b-4cb8-8760-e0614ded7060']
    except:
        return pd.DataFrame()

    #GOAL 3: REPORTS RELEASED MONTH TO DATE
    df_reports_released = df_reports[(df_reports['report_status'] == 'RELEASED') & (df_reports['state'] == 'RELEASED')]

    df_reports_released_current_month = df_reports_released[(df_reports_released['report_created_at'] >= first_day_current_month) & (df_reports_released['report_created_at'] < last_day_current_month + timedelta(days=1))]
    df_reports_released_current_month.index = df_reports_released_current_month['report_created_at']
    df_reports_released_current_month_daily = df_reports_released_current_month.resample('D').order_id.nunique()
    df_reports_released_current_month_daily.index = df_reports_released_current_month_daily.index.day
    while (len(df_reports_released_current_month_daily) < datetime.now().day):
        df_reports_released_current_month_daily = df_reports_released_current_month_daily.append(pd.Series([0]), ignore_index=True)
    df_reports_released_current_month = df_reports_released_current_month_daily.cumsum()
    #catch exception for first day of month
    try:
        if min(df_reports_released_current_month.index) < 1:
            df_reports_released_current_month.index += 1
        if min(df_reports_released_current_month_daily.index) < 1:
            df_reports_released_current_month_daily.index += 1
    except: pass

    df_reports_released_previous_month = df_reports_released[(df_reports_released['report_created_at'] >= first_day_previous_month) & (df_reports_released['report_created_at'] < last_day_previous_month + timedelta(days=1))]
    df_reports_released_previous_month.index = df_reports_released_previous_month['report_created_at']
    df_reports_released_previous_month_daily = df_reports_released_previous_month.resample('D').order_id.nunique()
    df_reports_released_previous_month_daily.index = df_reports_released_previous_month_daily.index.day
    df_reports_released_previous_month.index = df_reports_released_previous_month.index.day
    df_reports_released_previous_month = df_reports_released_previous_month_daily.cumsum()

    df_reports_released_mtd = pd.concat([df_reports_released_previous_month, df_reports_released_current_month, df_reports_released_current_month_daily, df_reports_released_previous_month_daily], axis=1)
    df_reports_released_mtd.columns = [['previous_month_count', 'current_month_count', 'current_month_daily', 'previous_month_daily']]
    df_reports_released_mtd['previous_month_count'] = df_reports_released_mtd['previous_month_count'].fillna(0)
    df_reports_released_mtd['previous_month_daily'] = df_reports_released_mtd['previous_month_daily'].fillna(0)

    #linreg trendline
    #catch exception for first day of month
    try:
        linear_regressor = LinearRegression()
        linear_regressor.fit(df_reports_released_mtd['current_month_count'].dropna().index.values.reshape(-1, 1), df_reports_released_mtd['current_month_count'].dropna().unstack().values.reshape(-1,1))
        Y_pred = linear_regressor.predict(df_reports_released_mtd['current_month_count'].index[:last_day_current_month.day].values.reshape(-1,1))
        predicted_values = pd.Series(Y_pred.flatten()).round(0)
        predicted_values.index = predicted_values.index + 1
        predicted_values = predicted_values[df_reports_released_mtd[df_reports_released_mtd['current_month_count'].isnull().any(axis=1)].index[0] - 1:]
        df_reports_released_mtd['predicted_count'] = predicted_values
    except: df_reports_released_mtd['predicted_count'] = ''

    return df_reports_released_mtd


def data_for_blocked_reports():
    merged_blocked = LabOpsDAO.get_blocked_reports_with_issue_type()
    merged_blocked_no_informative = merged_blocked[merged_blocked['issue_type'] != 'N']

    df_blocked_reports = pd.read_csv('~/data_pulls/lab_ops_metrics/blocked_reports.csv', parse_dates=[0, 1], index_col=0)
    df_blocked_reports = df_blocked_reports.append({'date': datetime.now().date(), 'smartgut_count': merged_blocked_no_informative[(merged_blocked_no_informative['kit_type'] == 16)].ssr.nunique(), 'smartjane_count': merged_blocked_no_informative[(merged_blocked_no_informative['kit_type'] == 17)].ssr.nunique()}, ignore_index=True)
    df_blocked_reports = df_blocked_reports.drop_duplicates(subset=['date'], keep='last')
    df_blocked_reports.to_csv('~/data_pulls/lab_ops_metrics/blocked_reports.csv')


def data_for_pipeline(date, kit_cutoff, sample_cutoff, report_cutoff, product):
    df_orders = LabOpsDAO.get_orders()
    df_kits = LabOpsDAO.get_kits()
    df_samples = LabOpsDAO.get_samples()
    df_reports = LabOpsDAO.get_released_reports()

    date = datetime.strptime(date, '%Y-%m-%d').date().replace(day=1)
    #date filter
    try:
        df_orders = df_orders[(df_orders['order_created_at'] >= pd.Timestamp(date)) & (df_orders['order_created_at'] < pd.Timestamp(date + relativedelta.relativedelta(months=1)))]
    except:
        return []

    #Product Filter
    try:
        if product == 'smartgut':
            df_orders = df_orders[df_orders['code'] == 'smart_gut']
            df_kits = df_kits[df_kits['item_type_id'] == '32708e12-4254-4d46-933a-f44d2ed32f5f']
            df_samples = df_samples[df_samples['kit_type'] == 16]
            df_reports = df_reports[df_reports['order_type_id'] == 'd93422aa-b3e7-4077-af20-61d560f73880']
        elif product == 'smartjane':
            df_orders = df_orders[df_orders['code'] == 'smart_jane']
            df_kits = df_kits[df_kits['item_type_id'] == 'd20ee363-ea4c-4411-ab71-cc68e8723670']
            df_samples = df_samples[df_samples['kit_type'] == 17]
            df_reports = df_reports[df_reports['order_type_id'] == 'fbc0caae-725b-4cb8-8760-e0614ded7060']
    except:
        return []

    df_orders_kits = pd.merge(df_orders, df_kits, how='left', on='delivery_id')
    df_orders_kits_samples = pd.merge(df_orders_kits, df_samples, how='left', on='sample_id')
    df_orders_kits_samples_reports = pd.merge(df_orders_kits_samples, df_reports[(df_reports['report_status'] == 'RELEASED') & (df_reports['state'] == 'RELEASED')], how='left', on='sample_id')
    df_pipeline = df_orders_kits_samples_reports

    df_pipeline['ship_date_minus_order_created_at'] = df_pipeline['ship_date'] - df_pipeline['order_created_at']
    df_pipeline['sample_received_minus_ship_date'] = df_pipeline['sample_received'] - df_pipeline['ship_date']
    df_pipeline['report_created_at_minus_sample_received'] = df_pipeline['report_created_at'] - df_pipeline['sample_received']

    #orders
    df_orders = df_pipeline[(datetime.now() - df_pipeline['order_created_at']) >= timedelta(days=(int(kit_cutoff) + int(sample_cutoff) + int(report_cutoff)))]
    orders = df_orders.order_id_x.nunique()
    #kits shipped
    df_kits_shipped = df_orders[df_orders['ship_date_minus_order_created_at'] <= timedelta(days=int(kit_cutoff))]
    kits_shipped = df_kits_shipped.order_id_x.nunique()
    #samples accessioned
    df_samples_accessioned = df_kits_shipped[df_kits_shipped['sample_received_minus_ship_date'] <= timedelta(days=int(sample_cutoff))]
    samples_accessioned = df_samples_accessioned.order_id_x.nunique()
    #reports released
    df_reports_released = df_samples_accessioned[df_samples_accessioned['report_created_at_minus_sample_received'] <= timedelta(days=int(report_cutoff))]
    reports_released = df_reports_released.order_id_x.nunique()

    return [orders, kits_shipped, samples_accessioned, reports_released]

def data_for_sample_accessioned_table(product):
    df_samples = LabOpsDAO.get_samples()
    #Product Filter
    try:
        if product == 'smartgut':
            df_samples = df_samples[df_samples['kit_type'] == 16]
        elif product == 'smartjane':
            df_samples = df_samples[df_samples['kit_type'] == 17]
    except:
        return pd.DataFrame()

    #METRIC 1: SAMPLES ACCESSIONED
    df_samples_accessioned = df_samples
    df_samples_accessioned.index = df_samples_accessioned['sample_received']
    df_samples_accessioned = pd.DataFrame(df_samples_accessioned.resample('M').sample_id.nunique())
    df_samples_accessioned = df_samples_accessioned.reset_index().rename(columns={'sample_received':'Sample Accessioned Month', 'sample_id': '# Samples Accessioned'})
    df_samples_accessioned = df_samples_accessioned[df_samples_accessioned['Sample Accessioned Month'] >= '2018-01-31']

    return df_samples_accessioned

def data_for_sample_return_rate_table(product):
    #Product Filter
    df_orders = LabOpsDAO.get_orders()
    df_kits = LabOpsDAO.get_kits()
    df_samples = LabOpsDAO.get_samples()
    try:
        if product == 'smartgut':
            df_orders = df_orders[df_orders['code'] == 'smart_gut']
            df_kits = df_kits[df_kits['item_type_id'] == '32708e12-4254-4d46-933a-f44d2ed32f5f']
            df_samples = df_samples[df_samples['kit_type'] == 16]
        elif product == 'smartjane':
            df_orders = df_orders[df_orders['code'] == 'smart_jane']
            df_kits = df_kits[df_kits['item_type_id'] == 'd20ee363-ea4c-4411-ab71-cc68e8723670']
            df_samples = df_samples[df_samples['kit_type'] == 17]
    except:
        return pd.DataFrame()

    #METRIC 2: SAMPLE RETURN RATE
    df_orders_kits = pd.merge(df_orders, df_kits, how='inner', on='delivery_id')
    df_orders_kits_samples = pd.merge(df_orders_kits, df_samples, how='left', on='sample_id')
    df_samples_by_ship_date = df_orders_kits_samples
    df_samples_by_ship_date.index = df_samples_by_ship_date['ship_date']
    df_sample_return_rate = pd.DataFrame(df_samples_by_ship_date.resample('M').sample_id.nunique() / df_samples_by_ship_date.resample('M').shipment_id.nunique())
    df_sample_return_rate = df_sample_return_rate.reset_index().rename(columns={'ship_date': 'Kit Shipped Month', 0: 'Sample Return Rate (Samples Accessioned / Kits Shipped)'})
    df_sample_return_rate = df_sample_return_rate[df_sample_return_rate['Kit Shipped Month'] >= '2018-01-31']
    df_sample_return_rate = df_sample_return_rate.round(2)

    return df_sample_return_rate

def data_for_sample_accession_timeline_table(product):
    df_orders = LabOpsDAO.get_orders()
    df_kits = LabOpsDAO.get_kits()
    df_samples = LabOpsDAO.get_samples()

    #Product Filter
    try:
        if product == 'smartgut':
            df_orders = df_orders[df_orders['code'] == 'smart_gut']
            df_kits = df_kits[df_kits['item_type_id'] == '32708e12-4254-4d46-933a-f44d2ed32f5f']
            df_samples = df_samples[df_samples['kit_type'] == 16]

        elif product == 'smartjane':
            df_orders = df_orders[df_orders['code'] == 'smart_jane']
            df_kits = df_kits[df_kits['item_type_id'] == 'd20ee363-ea4c-4411-ab71-cc68e8723670']
            df_samples = df_samples[df_samples['kit_type'] == 17]
    except:
        return pd.DataFrame()

    #METRIC 3: SAMPLE ACCESSION TIMELINE (SAMPLE ACCESSION DATE - KIT SHIPPED DATE)
    df_orders_kits = pd.merge(df_orders, df_kits, how='inner', on='delivery_id')
    df_orders_kits_samples = pd.merge(df_orders_kits, df_samples, how='left', on='sample_id')
    df_sample_accession_timeline = df_orders_kits_samples
    df_sample_accession_timeline = df_sample_accession_timeline[~df_sample_accession_timeline['order_flow'].isin(['trf_transcribed', 'doctor_transcribed'])]
    df_sample_accession_timeline['sample_accession_date_minus_kit_ship_date'] = (df_sample_accession_timeline['sample_received'] - df_sample_accession_timeline['ship_date']).dt.days #convert timedelta to days
    df_sample_accession_timeline.index = df_sample_accession_timeline['ship_date']
    df_sample_accession_timeline = pd.DataFrame(df_sample_accession_timeline.resample('M').sample_accession_date_minus_kit_ship_date.mean())
    df_sample_accession_timeline = df_sample_accession_timeline.reset_index().rename(columns={'ship_date': 'Kit Shipped Month', 'sample_accession_date_minus_kit_ship_date': 'Sample Accession Timeline (Sample Accession Date - Kit Shipped Date)'})
    df_sample_accession_timeline = df_sample_accession_timeline[df_sample_accession_timeline['Kit Shipped Month'] >= '2018-01-31']
    df_sample_accession_timeline = df_sample_accession_timeline.round(2)

    return df_sample_accession_timeline

def data_for_sample_process_success_table(product):
    df_orders = LabOpsDAO.get_orders()
    df_samples = LabOpsDAO.get_samples()
    df_results = LabOpsDAO.get_report_corrections()

    #Product Filter
    try:
        if product == 'smartgut':
            df_orders = df_orders[df_orders['code'] == 'smart_gut']
            df_samples = df_samples[df_samples['kit_type'] == 16]
        elif product == 'smartjane':
            df_orders = df_orders[df_orders['code'] == 'smart_jane']
            df_samples = df_samples[df_samples['kit_type'] == 17]
    except:
        return pd.DataFrame()

    #METRIC 4: SAMPLES PROCESSED SUCCESSFULLY
    df_orders_samples = pd.merge(df_orders, df_samples, how='inner', on='sample_id')
    df_orders_samples_results = pd.merge(df_orders_samples, df_results, how='inner', on='order_id')
    df_sample_process_success = df_orders_samples_results[df_orders_samples_results['sample_process_status'] == 'success']
    df_sample_process_success = df_sample_process_success.sort_values(by=['order_id', 'result_created_at'], ascending=True).drop_duplicates(subset=['order_id'], keep='first')
    df_sample_process_success.index = df_sample_process_success['result_created_at']
    df_sample_process_success = pd.DataFrame(df_sample_process_success.resample('M').order_id.nunique())
    df_sample_process_success = df_sample_process_success.reset_index().rename(columns={'result_created_at': 'Sample Processed Month', 'order_id': '# Samples Processed Successfully'})
    df_sample_process_success = df_sample_process_success[df_sample_process_success['Sample Processed Month'] >= '2018-01-31']

    return df_sample_process_success

def data_for_sample_process_failure_table(product, df_orders, df_samples):
    df_orders = LabOpsDAO.get_orders()
    df_samples = LabOpsDAO.get_samples()
    df_results = LabOpsDAO.get_report_corrections()

    #Product Filter
    try:
        if product == 'smartgut':
            df_orders = df_orders[df_orders['code'] == 'smart_gut']
            df_samples = df_samples[df_samples['kit_type'] == 16]
        elif product == 'smartjane':
            df_orders = df_orders[df_orders['code'] == 'smart_jane']
            df_samples = df_samples[df_samples['kit_type'] == 17]
    except:
        return pd.DataFrame()

    #METRIC 5: SAMPLES PROCESSED FAILURES
    df_orders_samples = pd.merge(df_orders, df_samples, how='inner', on='sample_id')
    df_orders_samples_results = pd.merge(df_orders_samples, df_results, how='inner', on='order_id')
    df_sample_process_failure = df_orders_samples_results[df_orders_samples_results['sample_process_status'].isin(['recollected', 'recollection', 'final-rejected'])]
    df_sample_process_failure = df_sample_process_failure.sort_values(by=['order_id', 'result_created_at'], ascending=True).drop_duplicates(subset=['order_id'], keep='first')
    df_sample_process_failure.index = df_sample_process_failure['result_created_at']
    df_sample_process_failure = pd.DataFrame(df_sample_process_failure.resample('M').order_id.nunique())
    df_sample_process_failure = df_sample_process_failure.reset_index().rename(columns={'result_created_at': 'Sample Processed Month', 'order_id': '# Sample Process Failures'})
    df_sample_process_failure = df_sample_process_failure[df_sample_process_failure['Sample Processed Month'] >= '2018-01-31']

    return df_sample_process_failure

def data_for_sample_process_success_rate_table(product):
    df_orders = LabOpsDAO.get_orders()
    df_samples = LabOpsDAO.get_samples()
    df_results = LabOpsDAO.get_report_corrections()


    #Product Filter
    try:
        if product == 'smartgut':
            df_orders = df_orders[df_orders['code'] == 'smart_gut']
            df_samples = df_samples[df_samples['kit_type'] == 16]
        elif product == 'smartjane':
            df_orders = df_orders[df_orders['code'] == 'smart_jane']
            df_samples = df_samples[df_samples['kit_type'] == 17]
    except:
        return pd.DataFrame()

    #METRIC 6: SAMPLES PROCESSED SUCCESSFULLY / TOTAL SAMPLES PROCESSED
    df_orders_samples = pd.merge(df_orders, df_samples, how='inner', on='sample_id')
    df_orders_samples_results = pd.merge(df_orders_samples, df_results, how='inner', on='order_id')
    df_orders_samples_results.index = df_orders_samples_results['result_created_at']
    df_sample_process_success_rate = pd.DataFrame(df_orders_samples_results[df_orders_samples_results['sample_process_status'] == 'success'].resample('M').order_id.nunique() / df_orders_samples_results.resample('M').order_id.nunique())
    df_sample_process_success_rate = df_sample_process_success_rate.reset_index().rename(columns={'result_created_at': 'Sample Processed Month', 'order_id': 'Sample Process Success Rate (Successfully Processed / Total Processed)'})
    df_sample_process_success_rate = df_sample_process_success_rate[df_sample_process_success_rate['Sample Processed Month'] >= '2018-01-31']
    df_sample_process_success_rate = df_sample_process_success_rate.round(2)

    return df_sample_process_success_rate

def data_for_sample_process_tat_table(product):
    df_orders = LabOpsDAO.get_orders()
    df_samples = LabOpsDAO.get_samples()
    df_results = LabOpsDAO.get_report_corrections()

    #Product Filter
    try:
        if product == 'smartgut':
            df_orders = df_orders[df_orders['code'] == 'smart_gut']
            df_samples = df_samples[df_samples['kit_type'] == 16]
        elif product == 'smartjane':
            df_orders = df_orders[df_orders['code'] == 'smart_jane']
            df_samples = df_samples[df_samples['kit_type'] == 17]
    except:
        return pd.DataFrame()

    #METRIC 7: SAMPLE PROCESSING TAT (SAMPLE PROCESSED DATE - SAMPLE ACCESSIONED DATE)
    df_orders_samples = pd.merge(df_orders, df_samples, how='inner', on='sample_id')
    df_orders_samples_results = pd.merge(df_orders_samples, df_results, how='inner', on='order_id')
    df_sample_process_tat = df_orders_samples_results.sort_values(by=['order_id', 'result_created_at'], ascending=True).drop_duplicates(subset=['order_id'], keep='first')
    df_sample_process_tat['sample_process_date_minus_sample_accession_date'] = (df_sample_process_tat['result_created_at'] - df_sample_process_tat['sample_received']).dt.days
    df_sample_process_tat.index = df_sample_process_tat['sample_received']
    df_sample_process_tat = pd.DataFrame(df_sample_process_tat.resample('M').sample_process_date_minus_sample_accession_date.mean())
    df_sample_process_tat = df_sample_process_tat.reset_index().rename(columns={'sample_received': 'Sample Accessioned Month', 'sample_process_date_minus_sample_accession_date': 'Sample Process Timeline (Sample Process Date - Sample Accession Date)'})
    df_sample_process_tat = df_sample_process_tat[df_sample_process_tat['Sample Accessioned Month'] >= '2018-01-31']
    df_sample_process_tat = df_sample_process_tat.round(2)

    return df_sample_process_tat

def data_for_reports_released_table(product):
    df_reports = LabOpsDAO.get_released_reports()

    #Product Filter
    try:
        if product == 'smartgut':
            df_reports = df_reports[df_reports['order_type_id'] == 'd93422aa-b3e7-4077-af20-61d560f73880']
        elif product == 'smartjane':
            df_reports = df_reports[df_reports['order_type_id'] == 'fbc0caae-725b-4cb8-8760-e0614ded7060']
    except:
        return pd.DataFrame()

    #METRIC 8: # OF REPORTS RELEASED
    df_reports_released = df_reports[(df_reports['report_status'] == 'RELEASED') & (df_reports['state'] == 'RELEASED')]
    df_reports_released.index = df_reports_released['report_created_at']
    df_reports_released = pd.DataFrame(df_reports_released.resample('M').order_id.nunique())
    df_reports_released = df_reports_released.reset_index().rename(columns={'report_created_at': 'Report Released Month', 'order_id': '# Reports Released'})
    df_reports_released = df_reports_released[df_reports_released['Report Released Month'] >= '2018-01-31']

    return df_reports_released

def data_for_report_release_timeline_table(product):
    df_orders = LabOpsDAO.get_orders()
    df_samples = LabOpsDAO.get_samples()
    df_kits = LabOpsDAO.get_kits()
    df_reports = LabOpsDAO.get_released_reports()

    #Product Filter
    try:
        if product == 'smartgut':
            df_orders = df_orders[df_orders['code'] == 'smart_gut']
            df_kits = df_kits[df_kits['item_type_id'] == '32708e12-4254-4d46-933a-f44d2ed32f5f']
            df_samples = df_samples[df_samples['kit_type'] == 16]
            df_reports = df_reports[df_reports['order_type_id'] == 'd93422aa-b3e7-4077-af20-61d560f73880']
        elif product == 'smartjane':
            df_orders = df_orders[df_orders['code'] == 'smart_jane']
            df_kits = df_kits[df_kits['item_type_id'] == 'd20ee363-ea4c-4411-ab71-cc68e8723670']
            df_samples = df_samples[df_samples['kit_type'] == 17]
            df_reports = df_reports[df_reports['order_type_id'] == 'fbc0caae-725b-4cb8-8760-e0614ded7060']
    except:
        return pd.DataFrame()

    #METRIC 9: REPORT RELEASE TIMELINE (REPORTS RELEASED TIMESTAMP - KITS SHIPPED)
    df_orders_kits = pd.merge(df_orders, df_kits, how='inner', on='delivery_id')
    df_orders_kits_samples = pd.merge(df_orders_kits, df_samples, how='inner', on='sample_id')
    df_orders_kits_samples_reports = pd.merge(df_orders_kits_samples, df_reports[(df_reports['report_status'] == 'RELEASED') & (df_reports['state'] == 'RELEASED')], how='inner', on='sample_id')
    df_report_release_timeline = df_orders_kits_samples_reports
    df_report_release_timeline['release_date_minus_ship_date'] = (df_report_release_timeline['report_created_at'] - df_report_release_timeline['ship_date']).dt.days
    df_report_release_timeline.index = df_report_release_timeline['ship_date']
    df_report_release_timeline = pd.DataFrame(df_report_release_timeline.resample('M').release_date_minus_ship_date.mean())
    df_report_release_timeline = df_report_release_timeline.reset_index().rename(columns={'ship_date': 'Kit Shipped Month', 'release_date_minus_ship_date': 'Report Release Timeline (Report Released Date - Kit Shipped Date)'})
    df_report_release_timeline = df_report_release_timeline[df_report_release_timeline['Kit Shipped Month'] >= '2018-01-31']
    df_report_release_timeline = df_report_release_timeline.round(2)

    return df_report_release_timeline

def data_for_report_corrections_table(product):
    df_reports = LabOpsDAO.get_released_reports()
    df_results = LabOpsDAO.get_report_corrections()

    #Product Filter
    try:
        if product == 'smartgut':
            df_reports = df_reports[df_reports['order_type_id'] == 'd93422aa-b3e7-4077-af20-61d560f73880']
            #df results is never used solo, so it is filtered on merges
        elif product == 'smartjane':
            df_reports = df_reports[df_reports['order_type_id'] == 'fbc0caae-725b-4cb8-8760-e0614ded7060']
            #df results is never used solo, so it is filtered on merges
    except:
        return pd.DataFrame()

    #METRIC 10: # OF REPORT CORRECTIONS
    df_reports_results = pd.merge(df_reports, df_results, how='inner', on='order_id')
    df_report_corrections = df_reports_results[df_reports_results['result_status'] == 'corrected']
    df_report_corrections.index = df_report_corrections['result_created_at']
    df_report_corrections = pd.DataFrame(df_report_corrections.resample('M').order_id.nunique())
    df_report_corrections = df_report_corrections.reset_index().rename(columns={'result_created_at': 'Report Correction Month', 'order_id': '# Reports Corrected'})
    df_report_corrections = df_report_corrections[df_report_corrections['Report Correction Month'] >= '2018-01-31']

    return df_report_corrections

def data_for_report_correction_rate(product):
    df_reports = LabOpsDAO.get_released_reports()
    df_results = LabOpsDAO.get_report_corrections()

    #Product Filter
    try:
        if product == 'smartgut':
            df_reports = df_reports[df_reports['order_type_id'] == 'd93422aa-b3e7-4077-af20-61d560f73880']
            #df results is never used solo, so it is filtered on merges
        elif product == 'smartjane':
            df_reports = df_reports[df_reports['order_type_id'] == 'fbc0caae-725b-4cb8-8760-e0614ded7060']
            #df results is never used solo, so it is filtered on merges
    except:
        return pd.DataFrame()

    #METRIC 11: REPORT CORRECTION RATE (CORRECTED REPORTS / TOTAL REPORTS)
    df_reports_results = pd.merge(df_reports, df_results, how='inner', on='order_id')
    df_report_correction_rate = df_reports_results
    df_report_correction_rate.index = df_report_correction_rate['report_created_at']
    df_report_correction_rate = pd.DataFrame(df_report_correction_rate[df_report_correction_rate['result_status'] == 'corrected'].resample('M').order_id.nunique() / df_report_correction_rate.resample('M').order_id.nunique())
    df_report_correction_rate = df_report_correction_rate.reset_index().rename(columns={'report_created_at': 'Initial Report Release Month', 'order_id': 'Report Correction Rate (Corrected Reports / Total Reports)'})
    df_report_correction_rate = df_report_correction_rate[df_report_correction_rate['Initial Report Release Month'] >= '2018-01-31']
    df_report_correction_rate = df_report_correction_rate.round(2)

    return df_report_correction_rate

########
title = 'Lab Ops Metrics'
functionality_description = 'Displays various metrics relating to Lab Ops.'
################################################################################

layout = html.Div([
    dbc.Card([
        dbc.CardHeader(title, style={'font-size':'2em'}),
        dbc.CardBody(
            [
                dbc.Button("Click here for more information on this dashboard", id="collapse-button_srm", className="mb-3"),
                dbc.Collapse(
                    [
                        dbc.CardText([
                            html.P(children=functionality_description),
                        ])
                    ],
                    id='collapse_srm',
                    is_open=False
                )
            ]
        )]),
    dbc.Tabs([
            dbc.Tab(
            [
                dbc.Row(
                    dbc.Col(
                        [
                            html.P(children='Product Filter:'),
                            dcc.Dropdown(
                                id='product_dropdown_state_srm_sample',
                                options=[
                                    {'label': 'SmartGut', 'value': 'smartgut'},
                                    {'label': 'SmartJane', 'value': 'smartjane'}
                                ],
                                value='smartgut',
                                style={'marginBottom': 10}
                            ),
                            html.Button(id='submit_button_srm_sample', n_clicks=0, children='Submit'),
                        ],
                        md=3,
                    ),
                ),
                dbc.Row([
                    dbc.Col(
                        [
                            html.Div(id='sample_accessioned_mtd_daily'),
                            dcc.Graph(
                                id='sample_accessioned_mtd_chart',
                                style={'height': 500, 'marginBottom': 20},
                            ),
                            dbc.Button("Chart Details", id="button_sample_chart_srm", className="mb-3"),
                            dbc.Collapse(
                                [
                                    html.H6('Data Pulled', style = {'marginBottom':0}),
                                    html.P(id='date_of_pull_srm_samples', children=time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime(os.path.expanduser('~/data_pulls/lab_ops_metrics/samples_data.csv'))))),

                                    html.Label(['Numbers shown are samples accessioned without the removal of samples with issues. Numbers may be slightly higher than those reported in the Goals Slack Channel, as samples with issues are removed there. Confirmed numbers with Erica Nunez. Link to Metabase query ', html.A('here', href='https://metabase.ubiome.io/question/2191?date_from=2018-01-01')]),
                                    html.P(children='*Predicted values are produced from linear regression of current month data.')
                                ],
                                id='collapse_sample_chart_srm',
                                is_open=False
                            )
                        ],
                    ),
                ]),
                html.Hr(),
                dbc.Row(
                    dbc.Col(
                        [
                            html.Div(id='sample_processed_successfully_mtd_daily'),
                            dcc.Graph(
                                id='sample_processed_successfully_mtd_chart',
                                style={'height': 500, 'marginBottom': 20},
                            ),
                            dbc.Button("Chart Details", id="button_sample_process_chart_srm", className="mb-3"),
                            dbc.Collapse(
                                [
                                    html.H6('Data Pulled', style = {'marginBottom':0}),
                                    html.P(id='date_of_pull_srm_orders', children=time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime(os.path.expanduser('~/data_pulls/lab_ops_metrics/orders_data.csv'))))),
                                    html.Label(['Samples are joined to Results, and successfully processed samples are defined as those with a \'sample_process_status\' of \'success\', with the date attributed to the sample accessioning date. Confirmed logic with Erica Nunez.']),
                                    html.P(children='*Predicted values are produced from linear regression of current month data.')
                                ],
                                id='collapse_sample_process_chart_srm',
                                is_open=False
                            )
                        ],
                    ),
                ),
            ], label='Samples'),
            dbc.Tab(
            [
                dbc.Row(
                    dbc.Col(
                        [
                            html.P(children='Product Filter:'),
                            dcc.Dropdown(
                                id='product_dropdown_state_srm_report',
                                options=[
                                    {'label': 'SmartGut', 'value': 'smartgut'},
                                    {'label': 'SmartJane', 'value': 'smartjane'}
                                ],
                                value='smartgut',
                                style={'marginBottom': 10}
                            ),
                            html.Button(id='submit_button_srm_report', n_clicks=0, children='Submit'),
                        ],
                        md=3,
                    ),
                ),
                dbc.Row(
                    dbc.Col(
                        [
                            html.Div(id='reports_released_mtd_daily'),
                            dcc.Graph(
                                id='reports_released_mtd_chart',
                                style={'height': 500, 'max-width': 1400, 'marginBottom': 20},
                            ),
                            dbc.Button("Chart Details", id="button_report_release_chart_srm", className="mb-3"),
                            dbc.Collapse(
                                [
                                    html.H6('Data Pulled', style = {'marginBottom':0}),
                                    html.P(id='date_of_pull_srm_reports', children=time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime(os.path.expanduser('~/data_pulls/lab_ops_metrics/reports_released_data.csv'))))),
                                    html.Label(['Daily numbers match those reported in the Goals Slack Channel. Confirmed numbers with Erica Nunez. Link to Metabase query ', html.A('here', href='https://metabase.ubiome.io/question/146?from=2019-02-08&to=2019-02-15')]),
                                    html.P(children='*Predicted values are produced from linear regression of current month data.')
                                ],
                                id='collapse_report_release_chart_srm',
                                is_open=False
                            )
                        ],
                        md=12
                    ),
                ),
                html.Hr(),
                dbc.Row([
                    dbc.Col(
                        [
                            html.Div(id='blocked_reports'),
                            dcc.Graph(
                                id='blocked_reports_chart',
                                style={'height': 500, 'marginBottom': 20},
                            ),
                            dbc.Button("Chart Details", id="button_blocked_reports_chart_srm", className="mb-3"),
                            dbc.Collapse(
                                [
                                    html.H6('Data Pulled', style = {'marginBottom':0}),
                                    html.P(id='date_of_pull_srm_blocked', children=time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime(os.path.expanduser('~/data_pulls/lab_ops_metrics/blocked_reports.csv'))))),
                                    html.Label(['A snapshot of the # of outstanding blocked reports each day. Confirmed numbers with Erica Nunez. Work is being done to produce the # of new blocked reports & the # of fixed reports daily.']),
                                    html.P(children='')
                                ],
                                id='collapse_blocked_reports_chart_srm',
                                is_open=False
                            )
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.Div(id='blocked_reports_issue_types'),
                            dcc.Graph(
                                id='blocked_reports_issue_types_chart',
                                style={'height': 500, 'marginBottom': 20},
                            ),
                            dbc.Button("Chart Details", id="button_blocked_reports_issue_types_chart_srm", className="mb-3"),
                            dbc.Collapse(
                                [
                                    html.H6('Data Pulled', style = {'marginBottom':0}),
                                    html.P(id='date_of_pull_srm_blocked_issue', children=time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime(os.path.expanduser('~/data_pulls/lab_ops_metrics/blocked_reports.csv'))))),
                                    html.Label(['Numbers are higher than chart on the left due to some reports being blocked for multiple issue types.']),
                                    html.P(children='')
                                ],
                                id='collapse_blocked_reports_issue_types_chart_srm',
                                is_open=False
                            ),
                            html.A(
                                'Download Data',
                                id='download_link',
                                download="reports_blocked_with_issue_type.csv",
                                href="",
                                target="_blank"
                            ),
                        ],
                        md=6,
                    ),
            ]),
            ], label='Reports'),
        dbc.Tab(
        [
            dbc.Col([
                dbc.Row([
                    dbc.Col(
                        [
                            html.P(children='Display:'),
                            dcc.Dropdown(
                                id='display_dropdown_state_srm_tat',
                                options=[
                                    {'label': 'Numbers', 'value': 'numbers'},
                                    {'label': 'Percentages', 'value': 'percentages'}
                                ],
                                value='numbers',
                                style={'marginBottom': 10}
                            ),
                            html.Button(id='submit_button_srm_tat', n_clicks=0, children='Refresh', style={'marginTop': '10px', 'marginBottom': '10px'}),
                        ],
                        md=3,
                    ),
                ]),
                dbc.Row([
                    dbc.Col([
                        html.Div(id='tat_table')
                    ], md=6)
                ])
            ])
        ], label='Samples Accessioned w/ Released Results Monthly TAT Report'),
    ]),
    dcc.Interval(
    id='interval_component_srm',
    interval=3600*1000,  # in milliseconds EVERY hour
    n_intervals=0
    ),
    dcc.Interval(
    id='interval_component_srm_expected_samples',
    interval=86400*1000,  # in milliseconds EVERY day
    n_intervals=0
    ),
    dcc.Interval(
    id='interval_component_srm_blocked_reports',
    interval=3600*1000,  # in milliseconds EVERY hour
    n_intervals=0
    ),
    dcc.Interval(
    id='interval_component_srm_slack_push',
    interval=3600*1000,  # in milliseconds EVERY hour
    n_intervals=0
    ),
    html.Div(id='hidden_div_srm', style={'display':'none'}),
    html.Div(id='hidden_div_srm_expected_samples', style={'display':'none'}),
    html.Div(id='hidden_div_srm_blocked_reports', style={'display':'none'}),
    html.Div(id='hidden_div_srm_slack_push', style={'display':'none'})
    ],
    className="mt-4",
    ),

@app.callback(
Output("collapse_srm", "is_open"),
[Input("collapse-button_srm", "n_clicks")],
[State("collapse_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_sample_chart_srm", "is_open"),
[Input("button_sample_chart_srm", "n_clicks")],
[State("collapse_sample_chart_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_sample_process_chart_srm", "is_open"),
[Input("button_sample_process_chart_srm", "n_clicks")],
[State("collapse_sample_process_chart_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_report_release_chart_srm", "is_open"),
[Input("button_report_release_chart_srm", "n_clicks")],
[State("collapse_report_release_chart_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_blocked_reports_chart_srm", "is_open"),
[Input("button_blocked_reports_chart_srm", "n_clicks")],
[State("collapse_blocked_reports_chart_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_blocked_reports_issue_types_chart_srm", "is_open"),
[Input("button_blocked_reports_issue_types_chart_srm", "n_clicks")],
[State("collapse_blocked_reports_issue_types_chart_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_tat_srm", "is_open"),
[Input("button_tat_srm", "n_clicks")],
[State("collapse_tat_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_sample_accession_table_srm", "is_open"),
[Input("button_sample_accession_table_srm", "n_clicks")],
[State("collapse_sample_accession_table_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_sample_return_rate_table_srm", "is_open"),
[Input("button_sample_return_rate_table_srm", "n_clicks")],
[State("collapse_sample_return_rate_table_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_sample_accession_timeline_table_srm", "is_open"),
[Input("button_sample_accession_timeline_table_srm", "n_clicks")],
[State("collapse_sample_accession_timeline_table_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_sample_process_success_srm", "is_open"),
[Input("button_sample_process_success_srm", "n_clicks")],
[State("collapse_sample_process_success_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_sample_process_failure_table_srm", "is_open"),
[Input("button_sample_process_failure_table_srm", "n_clicks")],
[State("collapse_sample_process_failure_table_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_sample_process_success_rate_table_srm", "is_open"),
[Input("button_sample_process_success_rate_table_srm", "n_clicks")],
[State("collapse_sample_process_success_rate_table_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_sample_process_tat_table_srm", "is_open"),
[Input("button_sample_process_tat_table_srm", "n_clicks")],
[State("collapse_sample_process_tat_table_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_reports_released_table_srm", "is_open"),
[Input("button_reports_released_table_srm", "n_clicks")],
[State("collapse_reports_released_table_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_report_release_timeline_table_srm", "is_open"),
[Input("button_report_release_timeline_table_srm", "n_clicks")],
[State("collapse_report_release_timeline_table_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_report_corrections_table_srm", "is_open"),
[Input("button_report_corrections_table_srm", "n_clicks")],
[State("collapse_report_corrections_table_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output("collapse_report_correction_rate_table_srm", "is_open"),
[Input("button_report_correction_rate_table_srm", "n_clicks")],
[State("collapse_report_correction_rate_table_srm", "is_open")])
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
Output('date_picker_state_srm_pipeline', 'max_date_allowed'),
[Input('kit_cutoff', 'value'),
Input('sample_cutoff', 'value'),
Input('report_cutoff', 'value')])
def update_date_picker_max_date(kit_cutoff, sample_cutoff, report_cutoff):
    return (datetime.now() - timedelta(int(kit_cutoff) + int(sample_cutoff) + int(report_cutoff))).date()

@app.callback(
Output('sample_accessioned_mtd_chart', 'figure'),
[Input('submit_button_srm_sample', 'n_clicks')],
[State('product_dropdown_state_srm_sample', 'value')])
def update_sample_accessioned_mtd_chart(submit_button, product):
    df_samples_accessioned_mtd = data_for_sample_accessioned_mtd_chart(product)

    return go.Figure(
        data=[
            go.Scatter(
                x=df_samples_accessioned_mtd.index,
                y=df_samples_accessioned_mtd.iloc[:,0],
                mode='lines',
                name='Previous Month to Date',
                marker=go.scatter.Marker(
                    color='#0098c8'
                )
            ),
            go.Scatter(
                x=df_samples_accessioned_mtd.index,
                y=df_samples_accessioned_mtd.iloc[:,1],
                mode='lines',
                name='Current Month to Date',
                marker=go.scatter.Marker(
                    color='#f7931e'
                )
            ),
            go.Scatter(
                x=df_samples_accessioned_mtd.index,
                y=df_samples_accessioned_mtd.iloc[:,2],
                mode='lines',
                name='Daily Count',
                marker=go.scatter.Marker(
                    color='#000000'
                )
            ),
            go.Scatter(
                x=df_samples_accessioned_mtd.index,
                y=df_samples_accessioned_mtd.iloc[:,4],
                mode='markers',
                name='Predicted Month to Date',
                marker=go.scatter.Marker(
                    color='#f7931e'
                )
            )
        ],
        layout=go.Layout(
            title=product + ' Samples Accessioned Month to Date',
            xaxis={'title': 'Day of Month'},
            yaxis={'title': '# Samples Accessioned'},
            showlegend=True,
            legend=go.layout.Legend(
                x=0,
                y=1
            ),
            margin=go.layout.Margin(l=100, r=100, t=50, b=50)
        )
    )

@app.callback(
Output('sample_processed_successfully_mtd_chart', 'figure'),
[Input('submit_button_srm_sample', 'n_clicks')],
[State('product_dropdown_state_srm_sample', 'value')])
def update_sample_processed_successfully_mtd_chart(submit_button, product):
    df_orders_samples_results_process_success_mtd = data_for_sample_processed_successfully_mtd_chart(product)

    return go.Figure(
        data=[
            go.Scatter(
                x=df_orders_samples_results_process_success_mtd.index,
                y=df_orders_samples_results_process_success_mtd.iloc[:,0],
                mode='lines',
                name='Previous Month to Date',
                marker=go.scatter.Marker(
                    color='#0098c8'
                )
            ),
            go.Scatter(
                x=df_orders_samples_results_process_success_mtd.index,
                y=df_orders_samples_results_process_success_mtd.iloc[:,1],
                mode='lines',
                name='Current Month to Date',
                marker=go.scatter.Marker(
                    color='#f7931e'
                )
            ),
            go.Scatter(
                x=df_orders_samples_results_process_success_mtd.index,
                y=df_orders_samples_results_process_success_mtd.iloc[:,2],
                mode='lines',
                name='Daily Count',
                marker=go.scatter.Marker(
                    color='#000000'
                )
            ),
            go.Scatter(
                x=df_orders_samples_results_process_success_mtd.index,
                y=df_orders_samples_results_process_success_mtd.iloc[:,4],
                mode='markers',
                name='Predicted Month to Date',
                marker=go.scatter.Marker(
                    color='#f7931e'
                )
            )
        ],
        layout=go.Layout(
            title=product + ' Samples Processed Successfully Month to Date',
            xaxis={'title': 'Day of Month'},
            yaxis={'title': '# Samples Processed Successfully'},
            showlegend=True,
            legend=go.layout.Legend(
                x=0,
                y=1
            ),
            margin=go.layout.Margin(l=100, r=100, t=50, b=50)
        )
    )

@app.callback(
Output('reports_released_mtd_chart', 'figure'),
[Input('submit_button_srm_report', 'n_clicks')],
[State('product_dropdown_state_srm_report', 'value')])
def update_reports_released_mtd_chart(submit_button, product):
    df_reports_released_mtd = data_for_reports_released_mtd_chart(product)

    return go.Figure(
        data=[
            go.Scatter(
                x=df_reports_released_mtd.index,
                y=df_reports_released_mtd.iloc[:,0],
                mode='lines',
                name='Previous Month to Date',
                marker=go.scatter.Marker(
                    color='#0098c8'
                )
            ),
            go.Scatter(
                x=df_reports_released_mtd.index,
                y=df_reports_released_mtd.iloc[:,1],
                mode='lines',
                name='Current Month to Date',
                marker=go.scatter.Marker(
                    color='#f7931e'
                )
            ),
            go.Scatter(
                x=df_reports_released_mtd.index,
                y=df_reports_released_mtd.iloc[:,2],
                mode='lines',
                name='Daily Count',
                marker=go.scatter.Marker(
                    color='#000000'
                )
            ),
            go.Scatter(
                x=df_reports_released_mtd.index,
                y=df_reports_released_mtd.iloc[:,4],
                mode='markers',
                name='Predicted Month to Date',
                marker=go.scatter.Marker(
                    color='#f7931e'
                )
            )
        ],
        layout=go.Layout(
            title=product + ' Reports Released Month to Date',
            xaxis={'title': 'Day of Month'},
            yaxis={'title': '# Reports Released'},
            showlegend=True,
            legend=go.layout.Legend(
                x=0,
                y=1
            ),
            margin=go.layout.Margin(l=100, r=100, t=50, b=50)
        )
    )

@app.callback(
Output('blocked_reports_chart', 'figure'),
[Input('submit_button_srm_report', 'n_clicks')],
[State('product_dropdown_state_srm_report', 'value')])
def update_blocked_reports_chart(submit_button, product):
    df_blocked_reports = pd.read_csv('~/data_pulls/lab_ops_metrics/blocked_reports.csv', parse_dates=['date'])

    df_blocked_reports = df_blocked_reports[df_blocked_reports['date'] >= (datetime.now() - timedelta(days=30))]

    if (product == 'smartgut'):
        return go.Figure(
            data=[
                go.Scatter(
                    x=df_blocked_reports['date'],
                    y=df_blocked_reports['smartgut_count'],
                    mode='lines',
                    name='Blocked Reports',
                    marker=go.scatter.Marker(
                        color='#f7931e'
                    )
                ),
            ],
            layout=go.Layout(
                title=product + ' Outstanding Blocked Reports',
                xaxis={'title': 'Date'},
                yaxis={'title': '# Blocked Reports'},
                showlegend=True,
                legend=go.layout.Legend(
                    x=1,
                    y=1
                ),
                margin=go.layout.Margin(l=100, r=100, t=50, b=50)
            )
        )
    elif (product == 'smartjane'):
        return go.Figure(
            data=[
                go.Scatter(
                    x=df_blocked_reports['date'],
                    y=df_blocked_reports['smartjane_count'],
                    mode='lines',
                    name='Blocked Reports',
                    marker=go.scatter.Marker(
                        color='#f7931e'
                    )
                ),
            ],
            layout=go.Layout(
                title=product + ' Outstanding Blocked Reports',
                xaxis={'title': 'Date'},
                yaxis={'title': '# Blocked Reports'},
                showlegend=True,
                legend=go.layout.Legend(
                    x=1,
                    y=1
                ),
                margin=go.layout.Margin(l=100, r=100, t=50, b=50)
            )
        )

@app.callback(
Output('blocked_reports_issue_types_chart', 'figure'),
[Input('submit_button_srm_report', 'n_clicks')],
[State('product_dropdown_state_srm_report', 'value')])
def update_blocked_reports_issue_types_chart(submit_button, product):
    df_blocked_reports = LabOpsDAO.get_blocked_reports_with_issue_type()

    merged_blocked_no_informative = df_blocked_reports[df_blocked_reports['issue_type'] != 'N']

    if (product == 'smartgut'):
        merged_blocked_no_informative = merged_blocked_no_informative[merged_blocked_no_informative['kit_type'] == 16]
    elif (product == 'smartjane'):
        merged_blocked_no_informative = merged_blocked_no_informative[merged_blocked_no_informative['kit_type'] == 17]

    df_blocked_reports_issues = merged_blocked_no_informative.groupby('issue_type_description').ssr.nunique().sort_values(ascending=False)

    return go.Figure(
        data=[
            go.Bar(
                x=df_blocked_reports_issues.index[:10],
                y=df_blocked_reports_issues.values[:10],
                marker=dict(
                    color='#0098c8',
                )
            )
        ],
        layout=go.Layout(
            title=product + ' Outstanding Blocked Reports by Issue Type',
            yaxis={'title': '# Blocked Reports'},
            margin=go.layout.Margin(l=100, r=100, t=50, b=50)
        )
    )

@app.callback(
Output('tat_table', 'children'),
[Input('submit_button_srm_tat', 'n_clicks')],
[State('display_dropdown_state_srm_tat', 'value')])
def update_tat_table(submit_button, display):
    #Set summary table to look at previous month
    first_day_previous_month, last_day_previous_month = month_dates()[2:]
    first_day_previous_month = first_day_previous_month.date()
    last_day_previous_month = last_day_previous_month.date()
    parameters = '?parameters=[{"type":"text","target":["variable",["template-tag","received_from"]],"value":"' + str(first_day_previous_month) + '"}, {"type":"text","target":["variable",["template-tag","received_to"]],"value":"' + str(last_day_previous_month) + '"}, {"type":"number","target":["variable",["template-tag","runs"]],"value":"1"}]'

    tat_table = LabOpsDAO.get_tat()

    tat_table = tat_table[['tat_in_days', 'sg_samples', 'sj_samples', 'exp_samples']]
    tat_table = tat_table.transpose()
    tat_table.reset_index(level=0, inplace= True)
    new_header = tat_table.iloc[0] #grab the first row for the header
    tat_table = tat_table[1:] #take the data less the header row
    tat_table.columns = new_header #set the header row as the df header

    tat_table['total_accessioned'] = tat_table['15 days or more'] + tat_table['8 - 14 days'] + tat_table['Up to 7 days']
    tat_table = tat_table[['tat_in_days', 'total_accessioned', 'Up to 7 days', '8 - 14 days', '15 days or more']]

    if display == 'percentages':
        tat_table['Up to 7 days'] = (tat_table['Up to 7 days'] / tat_table['total_accessioned']) * 100
        tat_table['8 - 14 days'] = (tat_table['8 - 14 days'] / tat_table['total_accessioned']) * 100
        tat_table['15 days or more'] = (tat_table['15 days or more'] / tat_table['total_accessioned']) * 100

        tat_table['Up to 7 days'] = tat_table['Up to 7 days'].astype(str) + '%'
        tat_table['8 - 14 days'] = tat_table['8 - 14 days'].astype(str) + '%'
        tat_table['15 days or more'] = tat_table['15 days or more'].astype(str) + '%'

    return [
        html.H6(children=str(datetime.strftime(first_day_previous_month,'%B %Y')) + ' Monthly Tat Report'),
        dash_table.DataTable(
            data=tat_table.to_dict('rows'),
            columns=[
                {'name': i, 'id': i} for i in tat_table.columns
            ]
        ),
    ]

@app.callback(
Output('download_link', 'href'),
[Input('submit_button_srm_report', 'n_clicks')],
[State('product_dropdown_state_srm_report', 'value')])
def update_download_link(submit_button, product):
    df_blocked_reports = LabOpsDAO.get_blocked_reports_with_issue_type()
    csv_string = df_blocked_reports.to_csv(index=False, encoding='utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string


'''
@app.callback(
Output('pipeline_chart', 'figure'),
[Input('submit_button_srm_pipeline', 'n_clicks')],
[State('date_picker_state_srm_pipeline', 'date'),
State('kit_cutoff', 'value'),
State('sample_cutoff', 'value'),
State('report_cutoff', 'value'),
State('product_dropdown_state_srm_pipeline', 'value')])
def update_pipeline(submit_button, date, kit_cutoff, sample_cutoff, report_cutoff, product):
    df_orders = pd.read_csv('data/current/samples_reports_metrics/orders_data.csv', parse_dates=['order_created_at'], parse_dates=['order_created_at'])
    df_kits = pd.read_csv('data/current/samples_reports_metrics/kits_data.csv', parse_dates=['ship_date'], parse_dates=['ship_date'])
    df_samples = pd.read_csv('data/current/samples_reports_metrics/samples_data.csv', parse_dates=['sample_received'], parse_dates=['sample_received'])
    df_reports = pd.read_csv('data/current/samples_reports_metrics/reports_data.csv', parse_dates=['report_created_at'], parse_dates=['report_created_at'])

    df_pipeline = data_for_pipeline(date, kit_cutoff, sample_cutoff, report_cutoff, product, df_orders, df_kits, df_samples, df_reports)

    # chart stages data
    values = df_pipeline
    phases = ['Orders', 'Kits Shipped', 'Samples', 'Reports']

    # color of each funnel section
    colors = ['#FFC20E', '#BFD730', '#0098C8', '#8781BD']

    n_phase = len(phases)
    plot_width = 400

    # height of a section and difference between sections
    section_h = 100
    section_d = 10

    # multiplication factor to calculate the width of other sections
    unit_width = plot_width / max(values)

    # width of each funnel section relative to the plot width
    phase_w = [int(value * unit_width) for value in values]

    # plot height based on the number of sections and the gap in between them
    height = section_h * n_phase + section_d * (n_phase - 1)

    # list containing all the plot shapes
    shapes = []

    # list containing the Y-axis location for each section's name and value text
    label_y = []

    for i in range(n_phase):
        if (i == n_phase-1):
                points = [phase_w[i] / 2, height, phase_w[i] / 2, height - section_h]
        else:
                points = [phase_w[i] / 2, height, phase_w[i+1] / 2, height - section_h]

        path = 'M {0} {1} L {2} {3} L -{2} {3} L -{0} {1} Z'.format(*points)

        shape = {
                'type': 'path',
                'path': path,
                'fillcolor': colors[i],
                'line': {
                    'width': 1,
                    'color': colors[i]
                }
        }
        shapes.append(shape)

        # Y-axis location for this section's details (text)
        label_y.append(height - (section_h / 2))

        height = height - (section_h + section_d)

    # For phase names
    label_trace = go.Scatter(
        x=[-350]*n_phase,
        y=label_y,
        mode='text',
        text=phases,
        textfont=dict(
            color='#0098c8',
            size=13
        ),
        hoverinfo='none'
    )

    # For phase values
    value_trace = go.Scatter(
        x=[350]*n_phase,
        y=label_y,
        mode='text',
        text=values,
        textfont=dict(
            color='#0098c8',
            size=13
        ),
        hoverinfo='none'
    )

    data = [label_trace, value_trace]

    layout = go.Layout(
        title= product + " Pipeline",
        titlefont=dict(
            size=20,
            color='#0098c8'
        ),
        hovermode='closest',
        shapes=shapes,
        showlegend=False,
        height=450,
        width=1000,
        paper_bgcolor='rgba(255,255,255, 1)',
        plot_bgcolor='rgba(255,255,255, 1)',
        xaxis=dict(
            showticklabels=False,
            zeroline=False,
            showgrid=False,
        ),
        yaxis=dict(
            showticklabels=False,
            zeroline=False,
            showgrid=False,
        ),
        margin=go.layout.Margin(l=100, r=100, t=50, b=50)
    )

    fig = go.Figure(data=data, layout=layout)

    return fig
'''

@app.callback(
Output('hidden_div_srm_blocked_reports', 'children'),
[Input('interval_component_srm_blocked_reports', 'n_intervals')])
def update_data_blocked_reports(n):
    data_for_blocked_reports()

@app.callback(
Output('hidden_div_srm_slack_push', 'children'),
[Input('interval_component_srm_slack_push', 'n_intervals')])
def slack_push(n):
    #slack updates for previous day's goals if between 12PM & 1PM Eastern Time
    if (datetime.now().time() >= datetime(1, 1, 1, 9, 0).time()) & (datetime.now().time() < datetime(1, 1, 1, 10, 0).time()): #9 to 10
        df_samples_accessioned_mtd_sg = data_for_sample_accessioned_mtd_chart('smartgut')
        df_samples_accessioned_mtd_sj = data_for_sample_accessioned_mtd_chart('smartjane')

        day = datetime.now().date() - timedelta(days=1)

        #samples accessioned
        title = 'Samples Accessioned ' + str(day)
        #handle first day of month
        if (datetime.now().date().day == 1):
            details = [
                    {
                    "color": "#0098C8",
                    "fields": [
                        {
                            "title": ":smartgut_icon: SmartGut Daily",
                            "value": str(df_samples_accessioned_mtd_sg.loc[df_samples_accessioned_mtd_sg.index == day.day, 'previous_month_daily'].values[0][0]),
                            "short": True
                        },
                        {
                            "title": ":smartgut_icon: SmartGut MTD",
                            "value": str(df_samples_accessioned_mtd_sg.loc[df_samples_accessioned_mtd_sg.index == day.day, 'previous_month_count'].values[0][0]),
                            "short": True
                        }
                    ],
                    },
                    {
                    "color": "#6950A1",
                    "fields": [
                        {
                            "title": ":smartjane_icon: SmartJane Daily",
                            "value": str(df_samples_accessioned_mtd_sj.loc[df_samples_accessioned_mtd_sj.index == day.day, 'previous_month_daily'].values[0][0]),
                            "short": True
                        },
                        {
                            "title": ":smartjane_icon: SmartJane MTD",
                            "value": str(df_samples_accessioned_mtd_sj.loc[df_samples_accessioned_mtd_sj.index == day.day, 'previous_month_count'].values[0][0]),
                            "short": True
                        }
                    ]
                    }
                    ]
        else: details = [
                {
                "color": "#0098C8",
                "fields": [
                    {
                        "title": ":smartgut_icon: SmartGut Daily",
                        "value": str(df_samples_accessioned_mtd_sg.loc[df_samples_accessioned_mtd_sg.index == day.day, 'current_month_daily'].values[0][0]),
                        "short": True
                    },
                    {
                        "title": ":smartgut_icon: SmartGut MTD",
                        "value": str(df_samples_accessioned_mtd_sg.loc[df_samples_accessioned_mtd_sg.index == day.day, 'current_month_count'].values[0][0]),
                        "short": True
                    }
                ],
                },
                {
                "color": "#6950A1",
                "fields": [
                    {
                        "title": ":smartjane_icon: SmartJane Daily",
                        "value": str(df_samples_accessioned_mtd_sj.loc[df_samples_accessioned_mtd_sj.index == day.day, 'current_month_daily'].values[0][0]),
                        "short": True
                    },
                    {
                        "title": ":smartjane_icon: SmartJane MTD",
                        "value": str(df_samples_accessioned_mtd_sj.loc[df_samples_accessioned_mtd_sj.index == day.day, 'current_month_count'].values[0][0]),
                        "short": True
                    }
                ]
                }
                ]

        df_reports_released_mtd_sg = data_for_reports_released_mtd_chart('smartgut')
        df_reports_released_mtd_sj = data_for_reports_released_mtd_chart('smartjane')
        df_blocked_reports = pd.read_csv('~/data_pulls/lab_ops_metrics/blocked_reports.csv', parse_dates=['date'])

        #reports released
        title = 'Reports Released ' + str(day)
        #handle first day of month
        if (datetime.now().date().day == 1):
            details = [
                    {
                    "color": "#0098C8",
                    "fields": [
                        {
                            "title": ":smartgut_icon: SmartGut Daily",
                            "value": str(df_reports_released_mtd_sg.loc[df_reports_released_mtd_sg.index == day.day, 'previous_month_daily'].values[0][0]),
                            "short": True
                        },
                        {
                            "title": ":smartgut_icon: SmartGut MTD",
                            "value": str(df_reports_released_mtd_sg.loc[df_reports_released_mtd_sg.index == day.day, 'previous_month_count'].values[0][0]),
                            "short": True
                        },
                        {
                            "title": ":smartgut_icon: SmartGut Outstanding Blocked",
                            "value": str(df_blocked_reports[df_blocked_reports['date'] == day]['smartgut_count'].values[0]),
                        },
                    ],
                    },
                    {
                    "color": "#6950A1",
                    "fields": [
                        {
                            "title": ":smartjane_icon: SmartJane Daily",
                            "value": str(df_reports_released_mtd_sj.loc[df_reports_released_mtd_sj.index == day.day, 'previous_month_daily'].values[0][0]),
                            "short": True
                        },
                        {
                            "title": ":smartjane_icon: SmartJane MTD",
                            "value": str(df_reports_released_mtd_sj.loc[df_reports_released_mtd_sj.index == day.day, 'previous_month_count'].values[0][0]),
                            "short": True
                        },
                        {
                            "title": ":smartjane_icon: SmartJane Outstanding Blocked",
                            "value": str(df_blocked_reports[df_blocked_reports['date'] == day]['smartjane_count'].values[0]),
                        },
                    ]
                    }
                    ]
        else: details = [
                {
                "color": "#0098C8",
                "fields": [
                    {
                        "title": ":smartgut_icon: SmartGut Daily",
                        "value": str(df_reports_released_mtd_sg.loc[df_reports_released_mtd_sg.index == day.day, 'current_month_daily'].values[0][0]),
                        "short": True
                    },
                    {
                        "title": ":smartgut_icon: SmartGut MTD",
                        "value": str(df_reports_released_mtd_sg.loc[df_reports_released_mtd_sg.index == day.day, 'current_month_count'].values[0][0]),
                        "short": True
                    },
                    {
                        "title": ":smartgut_icon: SmartGut Outstanding Blocked",
                        "value": str(df_blocked_reports[df_blocked_reports['date'] == day]['smartgut_count'].values[0]),
                    },
                ],
                },
                {
                "color": "#6950A1",
                "fields": [
                    {
                        "title": ":smartjane_icon: SmartJane Daily",
                        "value": str(df_reports_released_mtd_sj.loc[df_reports_released_mtd_sj.index == day.day, 'current_month_daily'].values[0][0]),
                        "short": True
                    },
                    {
                        "title": ":smartjane_icon: SmartJane MTD",
                        "value": str(df_reports_released_mtd_sj.loc[df_reports_released_mtd_sj.index == day.day, 'current_month_count'].values[0][0]),
                        "short": True
                    },
                    {
                        "title": ":smartjane_icon: SmartJane Outstanding Blocked",
                        "value": str(df_blocked_reports[df_blocked_reports['date'] == day]['smartjane_count'].values[0]),
                    },
                ]
                }
                ]
        print('slack push')

@app.callback(
Output('date_of_pull_srm_samples', 'children'),
[Input('interval_component_srm', 'n_intervals')])
def update_date_of_pull_samples(n):
    return time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime(os.path.expanduser('~/data_pulls/lab_ops_metrics/samples_data.csv'))))

@app.callback(
Output('date_of_pull_srm_orders', 'children'),
[Input('interval_component_srm', 'n_intervals')])
def update_date_of_pull_orders(n):
    return time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime(os.path.expanduser('~/data_pulls/lab_ops_metrics/orders_data.csv'))))

@app.callback(
Output('date_of_pull_srm_reports', 'children'),
[Input('interval_component_srm', 'n_intervals')])
def update_date_of_pull_reports(n):
    return time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime(os.path.expanduser('~/data_pulls/lab_ops_metrics/reports_released_data.csv'))))

@app.callback(
Output('date_of_pull_srm_blocked', 'children'),
[Input('interval_component_srm', 'n_intervals')])
def update_date_of_pull_blocked(n):
    return time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime(os.path.expanduser('~/data_pulls/lab_ops_metrics/blocked_reports.csv'))))

@app.callback(
Output('date_of_pull_srm_blocked_issue', 'children'),
[Input('interval_component_srm', 'n_intervals')])
def update_date_of_pull_blocked_issue(n):
    return time.strftime('%b %d, %Y %H:%M', time.localtime(os.path.getmtime(os.path.expanduser('~/data_pulls/lab_ops_metrics/blocked_reports.csv'))))
