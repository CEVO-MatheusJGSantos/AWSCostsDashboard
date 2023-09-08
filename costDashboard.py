from dash import Dash, dcc, html, callback, Input, Output, State
import plotly.express as px
import pandas as pd
import numpy as np
import boto3
from pprint import pprint
from datetime import datetime, date, time, timedelta
import argparse

argparser = argparse.ArgumentParser()
argparser.add_argument("-p", "--profile", help="AWS Profile", default=None)

if argparser.parse_args().profile is not None:
    session = boto3.Session(profile_name=argparser.parse_args().profile)
else:
    session = boto3.Session()
    
try:
    costExplorerClient = session.client('ce')
except Exception as error:
    raise error


(datetime.now() - timedelta(days=int(datetime.now().strftime("%d"))-1)).strftime("%Y-%m-%d")

periodStart = (datetime.now() - timedelta(days=int(datetime.now().strftime("%d")))).strftime("%Y-%m-01")
periodEnd = (datetime.now() - timedelta(days=int(datetime.now().strftime("%d")))).strftime("%Y-%m-%d")

def getUsageCost(startDate,endDate):
    try:
        # get the cost of usage and out-of-cycle charges for each service in the period requested
        UsageCost = costExplorerClient.get_cost_and_usage(
            TimePeriod={
                'Start': startDate,
                'End': endDate
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                    {
                        'Type':'DIMENSION',
                        'Key':'SERVICE'
                    }
                ],
                Filter={
                'Dimensions':{
                    'Key':'RECORD_TYPE',
                    'Values':['Usage','Out-of-cycle Charge']            
                    }
                },
            ).get('ResultsByTime')
    except Exception as error:
        raise error 

    # Generate a numpy array with the index for the dataframe, which is the data points related to the granularity
    DataframeIndex=np.array([dict['TimePeriod']['Start'] for dict in UsageCost])

    # Generate a numpy array with the list of all services returned by the cost explorer API, and remove the duplicated values
    DataframeColumns=np.unique(np.array(pd.json_normalize(UsageCost, record_path=['Groups','Keys'])[0]))

    # Creates a dict with all service names, assigning zero for all datapoints per service
    UsageCostData={}
    [UsageCostData.update({item:[float(0)]*len(DataframeIndex)}) for item in DataframeColumns]

    # Generates the Pandas dataframe with all services as columns, datapoints as rows and zero for all values
    UsageCostDataframe=pd.DataFrame(UsageCostData, index=DataframeIndex)

    # Iterates through the data returned by the cost explorer API and updates the values for each service by datapoint
    for timeStamp in DataframeIndex:
        id=np.where(DataframeIndex==timeStamp)[0][0]
        for value in UsageCost[id]['Groups']:
            for ServiceName in value['Keys']:
                UsageCostDataframe[ServiceName][timeStamp]=float("{:.2f}".format(float(value['Metrics']['UnblendedCost']['Amount'])))


    # Summarize total values per period
    newTotalsArray=UsageCostDataframe.sum(axis=1)

    #Define the minimum value threshold for the services
    valueThreshold = (np.mean(newTotalsArray.values)*0.01) # Should be 0.01 for monthly report

    # Summarizes all values below the threshold into a single "Others" column
    UsageCostDataframe['Others']=UsageCostDataframe[UsageCostDataframe.columns[UsageCostDataframe.sum()<valueThreshold]].sum(axis=1).values

    # Creating a new dataframe with only values above the threshold
    TopUsageCostDataframe=UsageCostDataframe[UsageCostDataframe.columns[UsageCostDataframe.sum() > valueThreshold]]

    # Sort the values in descending order
    TopUsageCostDataframe = TopUsageCostDataframe.sort_values(by=TopUsageCostDataframe.index[0],axis=1,ascending=False)

    return TopUsageCostDataframe


# Set up the Dash app
app = Dash(__name__)

# Set up the app layout
app.layout = html.Div(
    [
        html.Div(
            html.H1("Monthly Cost Explorer Dashboard")
        ),
        html.Div([
            html.Plaintext("Reporting period:"),
            dcc.DatePickerRange(
                id='date-picker-range',
                start_date=periodStart,
                end_date=periodEnd,
                max_date_allowed=datetime.now(),
            ),
            html.Button(id='button', n_clicks=0, children='Submit'),
    ]),
        html.Div(
            dcc.Graph(id='cost-graph', figure={}, className="row")
        ),
    ]
)

# Set up the callback function to update the graph
@app.callback(
    Output('cost-graph', 'figure'),
    (
        Input('button', 'n_clicks'),
        State('date-picker-range', 'start_date'),
        State('date-picker-range', 'end_date'))
)
def update_graph(n_clicks,start_date,end_date):
    if (end_date > start_date):
        TopUsageCostDataframe=getUsageCost(start_date,end_date)
        pprint(TopUsageCostDataframe.transpose())
    fig=px.pie(
        data_frame=TopUsageCostDataframe, 
        names=TopUsageCostDataframe.keys(), 
        values=TopUsageCostDataframe.values[0],
        title="Cost by Service: "+start_date+" - "+end_date,
        hole=0.3,
        width=1200,
        height=800,
        )
    fig.update_traces(
        textposition='inside', 
        textinfo='value',
        texttemplate='%{label}: $%{value:.2s}')
    fig.update_layout(legend=dict(
        yanchor="top",
        y=1,
        xanchor="left",
        x=-10
    ))
    return fig

app.run_server(debug=True)

