import pandas as pd
import numpy as np
import time

from seeq import spy

__all__ = ('update_worksheet_with_trends',)


def get_workbook(workbook_id:str, quiet:bool=True):
    """
    Get workbook.
    args:
        workbook_id (str): ID of workbook
        quiet (bool): quiet
    returns:
        workbook (seeq.spy.workbooks._workbook.Analysis)
    """
    wkb_df = spy.workbooks.search({'ID':workbook_id}, quiet=quiet)
    assert len(wkb_df) == 1, ValueError(
        'workbook_id, {}, is not unique in spy.workbooks.search'.format(workbook_id))
    workbook, *_ = spy.workbooks.pull(
        wkb_df, include_inventory = False, include_referenced_workbooks=False, quiet = quiet)

    return workbook

def get_worksheet_from_workbook(worksheet_id:'str', workbook:'seeq.spy.workbooks._workbook.Analysis', 
                                quiet:bool=True):
    """
    Get a specified worksheet from a workbook.
    args:
        worksheet_id (str): ID of desired worksheet
        workbook (seeq.spy.workbooks._workbook.Analysis): Workbook from which to retrieve

    returns:
        worksheet (seeq.spy.workbooks._worksheet.AnalysisWorksheet): Worksheet
    """
    worksheets = workbook.worksheets
    worksheet_ids = np.array([wk.id for wk in worksheets])
    where_worksheet_id = worksheet_ids == worksheet_id #indexer
    assert sum(where_worksheet_id) == 1, ValueError(
        'worksheet_id, {}, is not found in workbook {}, or is not unique'.format(worksheet_id, workbook))

    worksheet, *_ = np.array(worksheets)[where_worksheet_id]
    return worksheet

def update_worksheet_with_trends(trends_df:'pandas.DataFrame', wkb_id:'str', wks_id:'str', 
                                 progress_bar:'ipywidgets.widgets.widget_float.FloatProgress'=None):
    """docstring"""
    df = trends_df
    df = df.drop(columns=['isPartial'])
    df = df.rename(columns={x:'Google Trend: {}'.format(x) for x in df.columns})
    
    if progress_bar is not None:
        progress_bar.value=3
        progress_bar.description='Recovering Trends'
        time.sleep(.2)
    
    # find interpolation values
    index = df.index.values
    max_interp = max([index[i+1] - index[i] for i in range(len(index)-1)]) # find the max timedelta
    
    if progress_bar is not None:
        progress_bar.value=5
        progress_bar.description='Making Signals'
        time.sleep(.1)

    # worksheet info
    
    if progress_bar is not None:
        progress_bar.value=7
        progress_bar.description='Syncing with Seeq'
        time.sleep(.1)

    workbook = get_workbook(wkb_id)
    worksheet = get_worksheet_from_workbook(wks_id, workbook)

    # so we can include what already exists in the workbook:
    to_push = worksheet.display_items.copy()
    existing_google_trend_searches = to_push['Name'].values
            
    to_skip = set(
        existing_google_trend_searches
    ).intersection(
        set(df.columns.values)
    )
    
    if len(to_skip)!=0:
        print('Search term(s) {} already exist in worksheet. Skipping'.format([x.replace('Google Trend: ', '') for x in to_skip]))
        df = df.drop(columns=to_skip)
        
    if len(df.columns) == 0:
        if progress_bar is not None:
            progress_bar.value=10
            progress_bar.description = 'No new search'
        return

    # what we will add
    meta_data = pd.DataFrame(
        {'Maximum Interpolation':['7d' for i in df.columns], 
         'Name':df.columns.values, 
         'Type':['Signal' for i in df.columns]}
    )
    # Create signal with meta data
    returned = spy.push(metadata=meta_data, workbook=wkb_id, worksheet=wks_id, quiet=True)
    
    if progress_bar is not None:
        progress_bar.value=8
        progress_bar.description='Syncing with Seeq'
        time.sleep(.1)

    # rename columns to match ids (just created)
    mapper = {returned.at[ijk, 'Name']:returned.at[ijk, 'ID'] for ijk in returned.index}

    # push samples to signal
    result = spy.push(data=df.rename(columns=mapper), workbook=wkb_id, worksheet=wks_id, quiet=True)
    
    if progress_bar is not None:
        progress_bar.value=9
        progress_bar.description='Syncing with Seeq'
        time.sleep(.1)
    
    # add existing signals + conditions
    to_push = pd.concat((to_push, result[['Name', 'ID', 'Type']])).reset_index(drop=True)

    # final step
    results = spy.push(metadata=to_push, workbook=wkb_id, worksheet=wks_id, quiet=True)
    
    if progress_bar is not None:
        progress_bar.value=10
        progress_bar.description='Done!'
    
    return results
