import base64
import datetime
import io

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table

import pandas as pd


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
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
def update_figure(jsonified_cleaned_data):
    if jsonified_cleaned_data is not None:
        dff = pd.read_json(jsonified_cleaned_data, orient='split')
        #filtered_df = df[df.year == selected_year]
    traces = []
    #for i in dff.continent.unique():
    #    df_by_continent = dff[dff['continent'] == i]
    #traces.append(dict(
    #    x=dff['x'],
    #    y=dff['y'],
    #    text='test',
    #    mode='markers',
    #    opacity=0.7,
    #    marker={
    #        'size': 15,
    #        'line': {'width': 0.5, 'color': 'white'}
    #    },
    #    name='test'
    #))
    if jsonified_cleaned_data is not None:
        my_x=dff['x']
        my_y=dff['y']
    else:
        my_x=[1,2,3]
        my_y=[1,2,3]
    return {
    'data': [dict(
        x=my_x,
        y=my_y,
        text='test',
        mode='markers',
        marker={
            'size': 15,
            'opacity': 0.5,
            'line': {'width': 0.5, 'color': 'white'}
        }
    )],
    'layout': dict(
        xaxis={
            'title': 'test',
            'type': 'linear'
        },
        yaxis={
            'title': 'test',
            'type': 'linear'
        },
        margin={'l': 40, 'b': 40, 't': 10, 'r': 0},
        hovermode='closest'
    )
}
            #{
            #'data': traces,
            #'layout': dict(
            #    xaxis={'type': 'log', 'title': 'GDP Per Capita',
            #        'range':[2.3, 4.8]},
            #    yaxis={'title': 'Life Expectancy', 'range': [20, 90]},
            #    margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            #    legend={'x': 0, 'y': 1},
            #    hovermode='closest',
            #    transition = {'duration': 500},
            #)
if __name__ == '__main__':
    app.run_server(debug=True)