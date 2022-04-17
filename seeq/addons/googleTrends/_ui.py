from IPython.display import display, clear_output, HTML
from ipywidgets import VBox, HBox, widgets, Layout
import ipywidgets as widgets
import time

from ._funcs import update_worksheet_with_trends

__all__ = ('UI', )

def UI(pytrend:'pytrends.request.TrendReq', wkb_id:'str', wks_id:'str'):
    """docstring"""
    ### objects ###

    header = HTML(
        """
        <div>
            <h1>Google Trends in Seeq</h1><nl>
            <h4>Enter search words or phrased, separated by commas</h4>
        </div>
        """
    )

    kws = widgets.Text(
        value='',
        placeholder='Search Google Trends',
        description='Search Words:',
        disabled=False
    )

    search_button = widgets.Button(
        description='GO!',
        disabled=False,
        button_style='success', # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Click me',
        icon='' # (FontAwesome names without the `fa-` prefix)
    )

    reset_button = widgets.Button(
        description='Search again!',
        disabled=False,
        button_style='info', # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Click me',
        icon='' # (FontAwesome names without the `fa-` prefix)
    )


    progress_bar = widgets.FloatProgress(
        value=1,
        min=0,
        max=10.0,
        description='Contacting Google',
        bar_style='info',
        style={'bar_color': '#0000FF', 'description_width':'105px'},
        orientation='horizontal',
    )

    ### actions ### 

    def go(*args):    
        # do google trends sheet
        results = search(kws.value)
        if results is None:
            return

        kws.disabled = True
        search_button.disabled = True
        display(progress_bar)
        time.sleep(.1)

        # update seeq
        update_worksheet_with_trends(
            results, 
            wkb_id, 
            wks_id, 
            progress_bar=progress_bar
        )
        display(reset_button)
        return

    def search(comma_separated_text):
        search_terms = comma_separated_text.split(',')

        if len(search_terms)<1:
            print('Please enter a search term!!')
            return

        if len(search_terms)==1 and search_terms[0] == '':
            print('Please enter a search term!!')
            return

        search_terms = _clean_search_terms(search_terms)

        # Create payload and capture API tokens. 
        pytrend.build_payload(kw_list=search_terms)

        # Interest Over Time
        df = pytrend.interest_over_time()
        return df

    def reset(*args):
        clear_output()
        kws.disabled=False
        search_button.disabled=False
        display(header,kws,search_button)

    def _clean_search_terms(search_terms:'list'):
        clean_search_terms = []

        for term in search_terms:
            if term == '':
                continue
            thing = term
            # remove leading spaces
            try:
                while thing[0] == ' ':
                    thing = thing[1:]
            except IndexError:
                continue
            clean_search_terms.append(thing)

        return clean_search_terms


    ### assign actions ###

    search_button.on_click(go)
    reset_button.on_click(reset)

    ### display ###
    display(header,kws,search_button)