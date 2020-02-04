#import modules
import base64
import datetime
import io
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd

#config
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
mapbox_access_token = open("_mapbox_token").read()

#set the layout on the page
app.layout = html.Div([
    #first some information for the user about how to use the app
    html.H1('CSV Mapper'),
    html.P('Drag and drop a csv file for it to get plotted'),
    html.H5('Inputs:'),
    html.Li('csv file - that must have a Latitude and Longitude column'),
    html.H5('Outputs:'),
    html.Li('map - plots the Latitude and Longitude column'),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    dcc.Graph(id='output-data-plot'),
    html.Div(id='output-data-upload'),
    html.Div(id='intermediate-value', style={'display': 'none'}),
])

def parse_contents(contents, filename, date):
    """
    upload function that accepts csv or xls files
    
    returns:
        -   df: a dataframe
    """
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    return df

def update_table_format(df):
    """
    function cycles through the dataframe and writes to page
    """

    if df is not None:
        return html.Div([
            #html.H5(filename),
            #html.H6(datetime.datetime.fromtimestamp(date)),

            dash_table.DataTable(
                data=df.to_dict('records'),
                columns=[{'name': i, 'id': i} for i in df.columns]
            ),

            html.Hr()#,  # horizontal line

            ## For debugging, display the raw contents provided by the web browser
            #html.Div('Raw Content'),
            #html.Pre(contents[0:200] + '...', style={
            #    'whiteSpace': 'pre-wrap',
            #    'wordBreak': 'break-all'
            #})
        ])


@app.callback(Output('intermediate-value', 'children'),
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename'),
               State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        df = parse_contents(list_of_contents[0], list_of_names[0], list_of_dates[0])
        return df.to_json(date_format='iso', orient='split')
        #children = [
        #    parse_contents(c, n, d) for c, n, d in
        #    zip(list_of_contents, list_of_names, list_of_dates)]
        #return children

@app.callback(Output('output-data-upload', 'children'), [Input('intermediate-value', 'children')])
def update_table(jsonified_cleaned_data):
    if jsonified_cleaned_data is not None:
        # more generally, this line would be
        # json.loads(jsonified_cleaned_data)
        dff = pd.read_json(jsonified_cleaned_data, orient='split')
        table = update_table_format(dff)
        return table

@app.callback(Output('output-data-plot', 'figure'), [Input('intermediate-value', 'children')])
def gen_map(df):
    # groupby returns a dictionary mapping the values of the first field
    # 'classification' onto a list of record dictionaries with that
    # classification value.
    #import pdb; pdb.set_trace()
    if df is not None:
        dff = pd.read_json(df, orient='split')
        latitude = dff['Latitude'].values.tolist()
        longitude = dff['Longitude'].values.tolist()
    else:
        latitude = [-32.8882772]
        longitude = [151.765032]
    #outputs
    data_output = [{"type": "scattermapbox",
        "lat": latitude,
        "lon": longitude,
        "hoverinfo": "text",
    #   "hovertext": [["Name: {} <br>Type: {} <br>Provider: {}".format(i,j,k)]
    #                                for i,j,k in zip(map_data['Name'], map_data['Type'],map_data['Provider'])],
    #   "mode": "markers",
    #   "name": list(map_data['Name']),
        "marker": {
        "size": 6,
        "opacity": 0.7
        }}]

    layout_output = dict(
        autosize=True,
        height=500,
        font=dict(color="#191A1A"),
        titlefont=dict(color="#191A1A", size='14'),
        margin=dict(
            l=35,
            r=35,
            b=35,
            t=45
        ),
        hovermode="closest",
        plot_bgcolor='#fffcfc',
        paper_bgcolor='#fffcfc',
        legend=dict(font=dict(size=10), orientation='h'),
        title='WiFi Hotspots in NYC',
        mapbox=dict(
            accesstoken=mapbox_access_token,
            style="light",
            center=dict(
                lon=longitude[0],
                lat=latitude[0]
            ),
            zoom=10,
        ))
    return {"data": data_output, "layout": layout_output}

if __name__ == '__main__':
    app.run_server(debug=True)