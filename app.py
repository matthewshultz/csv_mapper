#import modules
import base64
import datetime
import io
import flask
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
from pyproj import Transformer
import csv
import urllib

#config
app = dash.Dash(
    __name__,
    external_stylesheets=[
        'https://codepen.io/chriddyp/pen/bWLwgP.css'
    ]
)
mapbox_access_token = open("_mapbox_token").read()

#set the layout on the page
app.layout = html.Div([
    #first some information for the user about how to use the app
    html.H1('CSV Mapper'),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '90%',
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
    html.Div(dcc.Graph(id='output-data-plot')),
    html.A('Download CSV', id = 'my-link'),
    html.Div(id='intermediate-value', style={'display': 'none'}),
    #have the input and output projections in the same row but different columns
    html.Div(id='test',
        className="does this do anything?",
        children=[
            html.Div(
                className="six columns",
                children=html.Div([
                    html.Div(
                        html.H3('Input Projection:'),
                    ),
                    dcc.RadioItems(id='input_proj', options=[
                        {'label': 'WGS84', 'value': 'epsg:4326'},
                        {'label': 'MGA Zone 56', 'value': 'epsg:28356'},
                        {'label': 'MGA Zone 55', 'value': 'epsg:28355'}],
                        value='epsg:4326'
                    )
                ])
            ),
            html.Div(
                className="six columns",
                children=html.Div([
                    html.Div(
                        html.H3('Output Projection:'),
                    ),
                    dcc.RadioItems(id='output_proj', options=[
                        {'label': 'WGS84', 'value': 'epsg:4326'},
                        {'label': 'MGA Zone 56 (mapping not supported)', 'value': 'epsg:28356'},
                        {'label': 'MGA Zone 55 (mapping not supported)', 'value': 'epsg:28355'}],
                        value='epsg:4326'
                    )#,
                    #html.Div([
                    #    html.Div(dcc.Input(id='input-box', type='text', value='temp.csv')),
                    #    html.Button('Export to file', id='button')],
                    #)
                ])
            )
        ]
    ),
    
    html.Div(id='output-data-upload'),
])

def determine_coordinate_columns(df, input_projection, output_projection):
    """
    function will determine the co ordiates used for updating the graph
    """
    #this is kind of cool but half done why not output a new df with the transfromed columns
    if (input_projection == 'epsg:4326') and ("Latitude" and "Longitude" in df.columns):
        x = "Latitude"
        y = "Longitude"
    elif (input_projection == 'epsg:28356') and ("Easting" and "Northing" in df.columns):
        x = "Easting"
        y = "Northing"
    elif (input_projection == 'epsg:28356') and ("EASTING" and "NORTHING" in df.columns):
        x = "EASTING"
        y = "NORTHING"
    else:
        raise Exception('Unable to determine spatial coordinates from file and config')

    mytransformer = Transformer.from_crs(input_projection, output_projection)
    x_out = []
    y_out = []
    for x_val, y_val in zip(df[x].values,  df[y].values):
        x_trans, y_trans = mytransformer.transform(x_val, y_val)
        x_out.append(x_trans)
        y_out.append(y_trans)            
    df['x_transformed'] = x_out
    df['y_transformed'] = y_out
    return df

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
"""
#if this is enabled we loose the ability to edit the input and output projections

@app.callback(Output('output-data-upload', 'children'), \
             [Input('intermediate-value', 'children'), \
              Input('input_proj', 'value')])
def update_table(jsonified_cleaned_data, input_projection):
    if jsonified_cleaned_data is not None:
        # more generally, this line would be
        # json.loads(jsonified_cleaned_data)
        dff = pd.read_json(jsonified_cleaned_data, orient='split')
        table = update_table_format(dff)
        return table
"""
@app.callback(Output('output-data-plot', 'figure'), \
    [Input('intermediate-value', 'children'), \
     Input('input_proj', 'value'), \
     Input('output_proj', 'value')])
def gen_map(df, input_projection, output_projection):
    # groupby returns a dictionary mapping the values of the first field
    # 'classification' onto a list of record dictionaries with that
    # classification value.
    #import pdb; pdb.set_trace()
    if df is not None:
        dff = pd.read_json(df, orient='split')
        #import pdb; pdb.set_trace()
        dff = determine_coordinate_columns(dff, input_projection, output_projection)
        
        latitude = dff['x_transformed'].values.tolist()
        longitude = dff['y_transformed'].values.tolist()
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
        title='Points in CSV file',
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

#@app.callback([dash.dependencies.Input('button', 'value'),\
#               dash.dependencies.Input('intermediate-value', 'children'),\
#               dash.dependencies.State('input-box', 'value')])
#def export_file(button, df, outputfile):
#    if df is not None:
#        dff = pd.read_json(df, orient='split')
#        dff.to_csv(outputfile, index=False)

#doesnt quite work as expected but i suppose it is pretty good

@app.callback(Output('my-link', 'href'), [Input('intermediate-value', 'children')])
def update_link(df):
    if df is not None:
        dff = pd.read_json(df, orient='split')
        csv_string = dff.to_csv(index=False, encoding='utf-8')
        csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
        return csv_string
        #return flask.send_file(csv_string,
        #                   mimetype='text/csv',
        #                   attachment_filename='downloadFile.csv',
        #                   as_attachment=True)
    #return '/dash/urlToDownload?value={}'.format(value)

#@app.server.route('/dash/urlToDownload')
#def download_csv():
#    import pdb; pdb.set_trace()
#    value = flask.request.args.get('value')
#    # create a dynamic csv or file here using `StringIO`
#    # (instead of writing to the file system)
#    str_io = io.StringIO()
#    str_io.write('You have selectedddd {}'.format(value))
#    mem = io.BytesIO()
#    mem.write(str_io.getvalue().encode('utf-8'))
#    mem.seek(0)
#    str_io.close()
#    csv_string = "data:text/csv;charset=utf-8," + urllib.Parse.quote(value)
#
#    return flask.send_file(csv_string,
#                           mimetype='text/csv',
#                           attachment_filename='downloadFile.csv',
#                           as_attachment=True)
    #row = ['hello', 'world']
    #proxy = io.StringIO()

    #writer = csv.writer(proxy)
    #writer.writerow(row)
#
    ## Creating the byteIO object from the StringIO Object
    #mem = io.BytesIO()
    #mem.write(proxy.getvalue().encode('utf-8'))
    ## seeking was necessary. Python 3.5.2, Flask 0.12.2
    #mem.seek(0)
    #proxy.close()
#
    #return send_file(
    #    mem,
    #    as_attachment=True,
    #    attachment_filename='test.csv',
    #    mimetype='text/csv'
    #)
if __name__ == '__main__':
    app.run_server(debug=True)