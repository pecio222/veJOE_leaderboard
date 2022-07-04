from dash import Dash, dcc, html, Input, Output, dash_table
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import time
from dash.dash_table.Format import Format, Group

app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG],
                meta_tags=[{'name': 'viewport',
                            'content': 'width=device-width, initial-scale=1.0, maximum-scale=1, minimum-scale=1,'}]
                            )
server = app.server
app.title = "veJOE Dashboard"

pieChartLayout1 = {
        'showlegend': True, 'legend': {'orientation': "h"}, 'title_x': 0.5, 'height': 600, 
        'paper_bgcolor': 'rgba(0,0,0,0)', 'font': {'color': 'rgba(255,255,255,1)'}
        }
pieChartLayoutTVLtotalFresh = {
        'showlegend': False, 'legend': {'orientation': "h"}, 'title_x': 0.5, 'height': 600, 
        'paper_bgcolor': 'rgba(0,0,0,0)', 'font': {'color': 'rgba(255,255,255,1)'},
        }
pieChartTraces1 = {'textposition': 'auto',  'textinfo': 'label+percent'}
lineChartLayout1 = {
        'showlegend': True, 'legend': {'orientation': "h", 'title': {'text': ""}}, 'title_x': 0.5, 'height': 600, 
        'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)', 
        'font': {'color': 'rgba(255,255,255,1)'}, 'coloraxis': {'colorbar': {'bgcolor': 'rgba(200,0,0,0)'}}, 
        'xaxis_title': None
        }
lineChartTraces1 = {}
x_axis_lauout = {'visible': True}


dropdown_style = {'textAlign':'center', 'backgroundColor': 'rgba(255,255,255,0.5)'}

development = True
if development:
    dataframesPath = "dataframes/"
    dataShowedPath = "dataShowed/"
else:
    dataframesPath = "mysite/dataShowed/"
    dataShowedPath = "mysite/dataShowed/"

df_fresh = pd.read_excel(f"{dataShowedPath}ready.xlsx")
df_JOEHolders = pd.read_excel(f"{dataShowedPath}joeHolders.xlsx")
df_historical_vejoe = pd.read_excel(f"{dataShowedPath}historicalvejoe.xlsx")
df_historical_TVL = pd.read_excel(f"{dataShowedPath}historicalTVL.xlsx")
df_TVL_merged = pd.concat([df_historical_TVL, df_fresh])

df_joes = df_fresh[['veJoeBalance', 'joeStaked', 'protocolName']].drop_duplicates()


df_TVL_merged = df_TVL_merged.drop(df_TVL_merged[df_TVL_merged.protocolName == 'others'].index)

df_total_vejoe_historical = df_historical_vejoe[['block', 'timestamp' , 'date' ,'vejoeTotalSupply']]
df_total_vejoe_historical = df_total_vejoe_historical.rename(columns={'vejoeTotalSupply': 'veJoeBalance'})
df_total_vejoe_historical['protocolName'] = 'all users'

joeHodlersChart = px.pie(df_JOEHolders, values='balance', names='name', 
        title='Where did JOE go?').update_layout(pieChartLayout1).update_traces(pieChartTraces1)

df_TVLTotal = pd.DataFrame([df_fresh['pairName'], df_fresh['TVL in masterchef']]).transpose().drop_duplicates()
# df_TVLTotal = df_TVLTotal.round({'TVL in masterchef': 0})
# print(df_TVLTotal)
df_TVLTotal.sort_values(by='TVL in masterchef', axis=0, ascending=False, inplace=True)


df_tvl_sum = df_fresh.groupby(by=['protocolName'], axis=0).sum()['protocol TVL'].reset_index()
df_Leaderboard = pd.merge(df_tvl_sum, df_joes)
df_Leaderboard = df_Leaderboard.drop(df_Leaderboard[df_Leaderboard.protocolName == 'all users'].index)

df_total_protocols_tvl = df_Leaderboard

df_Leaderboard = df_Leaderboard.drop(df_Leaderboard[df_Leaderboard.protocolName == 'others'].index)
df_Leaderboard = df_Leaderboard.sort_values('veJoeBalance', ascending=0).round(0)

df_total_protocols_tvl['pairName'] = 'all pools'

df_TVLFresh1 = df_fresh.drop(df_fresh[df_fresh.protocolName == 'all users'].index)

df_TVLFresh1 = pd.concat([df_TVLFresh1, df_total_protocols_tvl])
df_TVLFresh1.reset_index(inplace=True)





farmsTVLChart = px.pie(df_TVLTotal, values='TVL in masterchef', names='pairName', 
        title='Total Value Locked - All Deposits').update_layout(pieChartLayoutTVLtotalFresh).update_traces(pieChartTraces1)

lastUpdatedBlock = max(df_TVL_merged['block'])
lastUpdatedDate = max(df_TVL_merged['date'].dropna())
#lastUpdatedDate = datetime.fromtimestamp(max(df_TVL_merged['timestamp']))

colors = {
    'background': '#243447',
    'text': '#7FDBFF'
}

app.layout = html.Div(style = {'backgroundColor': colors['background'], 'max-width': 1440, 'margin': 'auto'}, children=[
        dbc.Row([
            dbc.Col(dcc.Loading(html.Img(src=app.get_asset_url('HighresScreenshot00017.png'), style = {'width': '100%'})),
                        xl={'size': 6,  "offset": 3, 'order': 'first'}, width={'size': 12, 'offset': 0, 'order': 'first'},
                        ),
            
            dbc.Col(html.H2("JOE Wars Dashboard", id='joe-dashboard'),
                        width={'size': 12, 'offset': 0}, style = {'textAlign':'center'}
                        ),

                        ]
                ),
        dbc.Row([            
            dbc.Col(html.H4("Leaderboard"),
                        width={'size': 12, 'offset': 0}, style = {'textAlign':'center'}
                        ),

                        ]
                ),
            
        dbc.Row([
                dbc.Col(dash_table.DataTable(
                    data = df_Leaderboard.to_dict('records'), 
                    # columns = [{"name": i, "id": i,'type':'numeric', 'format': {'specifier': ',.0f'}}  
                    #             if i not in ['protocolName'] else {"name": i, "id": i} for i in 
                    #             df_Leaderboard.columns],

                    columns = [{"name": 'Protocol', "id": 'protocolName'},
                    {"name": 'veJOE balance', "id": 'veJoeBalance', 'type':'numeric', 'format': {'specifier': ',.0f'}},  
                    {"name": 'JOE in veJOE', "id": 'joeStaked', 'type':'numeric', 'format': {'specifier': ',.0f'}},    
                    {"name": 'protocol TVL', "id": 'protocol TVL', 'type':'numeric', 'format': {'specifier': ',.0f'}},  
],
                    style_cell={
                            'height': 'auto', 'minWidth': '30px', 'width': '30px', 'maxWidth': '30px', 'whiteSpace': 'normal',
                            'textAlign': 'center',
                            'backgroundColor': 'rgba(255,255,255,0.2)',
                            'color': 'rgba(255,255,255,1)'
                        },         
                        editable=True,
                        sort_action="native"
                        ),
                        xl={'size': 6,  "offset": 3, 'order': 'first'}, width={'size': 12, 'offset': 0, 'order': 'first'}
                        )]),




        dbc.Row(
            [
                dbc.Col(dcc.Loading(dcc.Graph(figure=joeHodlersChart)),
                        xl={'size': 6, "offset": 3, 'order': 'first'}, width={'size': 12, 'offset': 0, 'order': 'first'}
                        
                        ),
            ]
        ),

        dbc.Row(html.H2("")
        ),

        dbc.Row(
            [
                dbc.Col([dcc.Loading(dcc.Graph(id="JOEInveJOEBalanceChart"))],
                        xl={'size': 5, "offset": 1, 'order': 'first'}, width={'size': 12, 'offset': 0, 'order': 'first'}
                        ),
                dbc.Col([dcc.Loading(dcc.Graph(id='veJOEBalanceChart')),],
                        xl={'size': 5, "offset": 0, 'order': 'last'}, width={'size': 12, 'offset': 0, 'order': 'first'}
                        ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Checklist(id='JOEInveJOEBalanceChart checkbox', options=[{'label': 'Hide other users', 'value': 'hide'}], value=['hide']),
                    xl={'size': 2, "offset": 5, 'order': 'first'}, width={'size': 6, 'offset': 3, 'order': 'first'}
                ),
                # dbc.Col(
                #     dcc.Checklist(id='veJOEBalanceChart checkbox', options=[{'label': 'Hide other users', 'value': 'hide'}], value=['hide']),
                #     xl={'size': 2, "offset": 3, 'order': 'last'}, width={'size': 4, 'offset': 4, 'order': 'first'}
                # ),

        ]

        ),

        dbc.Row(html.H2("")
        ),
        dbc.Row(
            [
                dbc.Col([dcc.Loading(dcc.Graph(figure=farmsTVLChart))],
                        xl={'size': 5,  "offset": 1, 'order': 'first'}, width={'size': 12, 'offset': 0, 'order': 'first'}
                        ),
                # dbc.Col(dash_table.DataTable(df_TVLTotal.to_dict('records')),
                #         width={'size': 3,  "offset": 0, 'order': 'last'}
                #         ),
                dbc.Col([dcc.Loading(dcc.Graph(id="TVL Fresh")),
                        ],
                        xl={'size': 5,  "offset": 0, 'order': 'last'}, width={'size': 12, 'offset': 0, 'order': 'first'}
                        ),

            ]
        ),
        dbc.Row(html.H2("")
        ),

        dbc.Row([    
                dbc.Col([dcc.Dropdown(id='TVL Fresh Pools',
                        options=df_TVLFresh1['pairName'].unique(),
                        value="all pools", clearable=False, style = dropdown_style
                        ),],
                        xl={'size': 2,  "offset": 7, 'order': 'first'}, width={'size': 6,  "offset": 3, 'order': 'last'}, align = 'center'
                        ),
                dbc.Col([            
                        dcc.Checklist(id='TVL Fresh checkbox', options=[{'label': 'Hide other users', 'value': 'hide'}], value=['hide'])],
                        xl={'size': 2,  "offset": 0, 'order': 'first'}, width={'size': 6,  "offset": 3, 'order': 'last'}, align = 'center'
                        ),

            ]
        ),
        dbc.Row(html.H2("")
        ),
        dbc.Row(html.H2("Historical balances", style = {'textAlign':'center'})
        ),


        dbc.Row(
            [
                dbc.Col([dcc.Loading(dcc.Graph(id='veJOEHistoricalBalanceChart'))],
                        xl={'size': 8,  "offset": 1, 'order': 'first'}, width={'size': 12, 'offset': 0, 'order': 'first'}
                        ),
                dbc.Col([dcc.Checklist(id='veJOEHistoricalBalanceChart checkbox', options=[{'label': 'Hide other users', 'value': 'hide'}], value=['hide'])],
                        xl={'size': 2,  "offset": 0, 'order': 'first'}, width={'size': 6,  "offset": 3, 'order': 'last'}, align = 'center'
                        ),


            ]
        ),
        dbc.Row(html.H2("")
        ),

        dbc.Row(
            [
                dbc.Col([dcc.Loading(dcc.Graph(id="historical TVL")),],
                        xl={'size': 8,  "offset": 1, 'order': 'first'}, width={'size': 12, 'offset': 0, 'order': 'first'}
                        ),
                dbc.Col([
                        
                        dcc.Dropdown(id='historical TVL dropdown',
                        options=df_TVL_merged['pairName'].dropna().unique(),
                        value='all pools', clearable=False, style = dropdown_style
                        ),
                        dcc.Checklist(id='historical TVL checkbox', options=[{'label': 'Hide other users', 'value': 'hide'}], value=['hide']                  
                        ),
                        html.A(dbc.Button('Go to top', id='go-top-btn', className='btn btn-orange align-middle btn btn-secondary'), href='#joe-dashboard'),
                        
                        
                        ],
                        xl={'size': 2,  "offset": 0, 'order': 'first'}, width={'size': 6,  "offset": 3, 'order': 'last'}, align = 'center'
                        ),
                        
            ]
        ),
        dbc.Row(html.H2("")
        ),

        dbc.Row(
            [
                dbc.Col([
          
            dcc.Markdown(f"""
            Last updated at {lastUpdatedDate} GMT - block {lastUpdatedBlock}

            Site still under development, more features to come. Also, frontend will change.

            JOE Wars image - Burasuko#4637 on Discord or [Unn4m3dL4L4 on Twitter](https://twitter.com/Unn4m3dL4L4), check out his other works.

            If you want to know more about JOE Wars, visit [official docs](https://docs.traderjoexyz.com/main/trader-joe/staking/vejoe-staking) or [Trader Joe's Twitter](https://twitter.com/traderjoe_xyz)."""),
            dcc.Markdown(""),
            dcc.Markdown("If you have any ideas to implement or found a bug, contact me on [Twitter](https://twitter.com/pecio222) or Discord - pecio33#5843")
                ], xl={'size': 6,  "offset": 6, 'order': 'last'}, width={'size': 12,  "offset": 0, 'order': 'last'})
            ]
                ),
])



@app.callback(
    Output("JOEInveJOEBalanceChart", "figure"), 
    [Input("JOEInveJOEBalanceChart checkbox", "value")],)
def generate_joe_in_veJOE_chart(showOthers):
    df_joes1 = df_joes
    if showOthers == ['hide']:
        df_joes1 = df_joes1.drop(df_joes1[df_joes1.protocolName == 'others'].index)
    JOEInveJOEBalanceChart = px.pie(df_joes1, values='joeStaked', names='protocolName', 
            title='JOE staked in veJOE').update_layout(pieChartLayout1).update_traces(pieChartTraces1)    

    return JOEInveJOEBalanceChart


@app.callback(
    Output("veJOEBalanceChart", "figure"), 
    [Input("JOEInveJOEBalanceChart checkbox", "value")],)
def generate_veJOE_balance_chart(showOthers):
    df_joes1 = df_joes
    if showOthers == ['hide']:
        df_joes1 = df_joes1.drop(df_joes1[df_joes1.protocolName == 'others'].index)
    veJOEBalanceChart = px.pie(df_joes1, values='veJoeBalance', names='protocolName', 
         title='veJOE balance').update_layout(pieChartLayout1).update_traces(pieChartTraces1)
    return veJOEBalanceChart




df_veJOE_merged = pd.concat([df_historical_vejoe, df_fresh, df_total_vejoe_historical])
df_veJOE_merged = df_veJOE_merged.drop(df_veJOE_merged[df_veJOE_merged.protocolName == 'others'].index)
df_veJOE_merged = df_veJOE_merged.drop(columns={'Unnamed: 0'})
df_veJOE_merged = df_veJOE_merged.sort_values(by='block', axis=0, ascending=True, inplace=False).reset_index()

@app.callback(
    Output("veJOEHistoricalBalanceChart", "figure"), 
    [Input("veJOEHistoricalBalanceChart checkbox", "value")],)
def generate_veJOE_historical_chart(showOthers):
    df_veee = df_veJOE_merged

    if showOthers == ['hide']:
        df_veee = df_veee.drop(df_veee[df_veee.protocolName == 'all users'].index)
    
    veJOEHistoricalBalanceChart = px.line(df_veee, x='date', y="veJoeBalance", 
            title="veJOE balances", color='protocolName').update_layout(lineChartLayout1).update_traces(lineChartTraces1).update_xaxes(x_axis_lauout)
    return veJOEHistoricalBalanceChart






@app.callback(
    Output("TVL Fresh", "figure"), 
    [Input("TVL Fresh Pools", "value"),
    Input("TVL Fresh checkbox", "value")],)
def generate_TVL_chart(pools, showOthers):
    
    df_TVLFresh2 = df_TVLFresh1.loc[df_TVLFresh1['pairName'] == pools]
    if showOthers == ['hide']:
        df_TVLFresh2 = df_TVLFresh2.drop(df_TVLFresh2[df_TVLFresh2.protocolName == 'others'].index)
    if pools == 'all pools':
        title_tvl = f'Total Value Locked in all boosted farms'
    else:
        title_tvl = f'Total Value Locked in {pools} farm'



    fig = px.pie(df_TVLFresh2, values='protocol TVL', names='protocolName', title=title_tvl).update_layout(pieChartLayout1).update_traces(pieChartTraces1)
    return fig


@app.callback(
    Output("historical TVL", "figure"), 
    Input("historical TVL dropdown", "value"),
    Input("historical TVL checkbox", "value"),
    )
def generate_historical_TVL_chart(pools, showOthers):
    df2 = df_TVL_merged.loc[df_TVL_merged['pairName'] == pools]
    if showOthers == ['hide']:
        df2 = df2.drop(df2[df2.protocolName == 'all users'].index)
        #print(df2)

    if pools == 'all pools':
        title_tvl = f'Total Value Locked in all boosted farms'
    else:
        title_tvl = f'Total Value Locked in {pools} farm'


    fig = px.line(df2, x='date', y='protocol TVL', 
            title=title_tvl, color='protocolName').update_layout(lineChartLayout1).update_traces(lineChartTraces1).update_xaxes(x_axis_lauout)
    return fig


if __name__ == '__main__':
    app.run_server(debug=development)



