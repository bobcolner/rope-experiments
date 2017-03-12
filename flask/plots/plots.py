import pandas as pd
import plotly
import plotly.graph_objs as go
import colorlover as cl
"""
output_type == 'notebook' | 'index' | 'div'
"""


def plot_boxplot(exp, output_type='div'):

    def get_box(cond):
        return go.Box(
            y=[cond['p05'], cond['p25'], cond['p50'], cond['p75'], cond['p95']],
            x=[cond['experiment']] * 5,
            name=cond['config']
        )

    data = [get_box(cond) for idx, cond in exp.iterrows()]

    if pd.isnull(exp.iloc[0]['client']):
        title = exp.iloc[0]['site_id'] + ' | ' + exp.iloc[0]['namespace']
    else:
        title = exp.iloc[0]['client'] + ' | ' + exp.iloc[0]['namespace']

    layout = go.Layout(
        title=title,
        yaxis=dict(
            title='CTOR',
            zeroline=False,
            gridcolor='#bdbdbd'
        ),
        xaxis=dict(showticklabels=True),
        showlegend=True,
        legend=dict(orientation="h"),
        font=dict(
            family='Courier New, monospace',
            size=14,
            color='#7f7f7f'
        ),
        boxmode='group'
        # height=400
    )
    fig = go.Figure(data=data, layout=layout)
    return output_options(output_type, data, fig)


def plot_timeseries(exp_hourly, stop_time=None, output_type='div'):
    data = []
    color_scale = cl.scales['9']['qual']['Set1'] * 3
    n = 0
    for _, config_hourly in exp_hourly.groupby(['config']):
        n = n + 1
        upper_ci = go.Scatter(
            name='95th',
            x=config_hourly['event_time'],
            y=config_hourly['p95'],
            mode='lines',
            marker=dict(color="444"),
            line=dict(width=0),
            fillcolor=color_scale[n].replace(')', ',0.3)').replace('rgb', 'rgba'),
            fill='tonexty',
            showlegend=False,
            legendgroup=config_hourly.iloc[0]['config']
        )
        mid_point = go.Scatter(
            name=config_hourly.iloc[0]['config'],
            x=config_hourly['event_time'],
            y=config_hourly['p50'],
            text=config_hourly['precision90'],
            textposition='bottom',
            mode='lines',
            line=dict(color=color_scale[n]),
            fillcolor=color_scale[n].replace(')', ',0.3)').replace('rgb', 'rgba'),
            fill='tonexty',
            showlegend=True,
            legendgroup=config_hourly.iloc[0]['config']
        )
        lower_ci = go.Scatter(
            name='5th',
            x=config_hourly['event_time'],
            y=config_hourly['p05'],
            marker=dict(color="444"),
            line=dict(width=0),
            mode='lines',
            showlegend=False,
            legendgroup=config_hourly.iloc[0]['config']
        )
        data = data + [lower_ci, mid_point, upper_ci]

    vlines = []
    send_lines = annotate_sends(exp_hourly)
    if send_lines:
        vlines = vlines + send_lines
    if stop_time:
        vlines = vlines + annotate_stop(stop_time)
        exp_results = 'Experiment Stopped'
    else:
        exp_results = 'Experiment Running'

    if pd.isnull(config_hourly.iloc[0]['client']):
        title = config_hourly.iloc[0]['site_id'] + ' | ' + config_hourly.iloc[0]['experiment']
    else:
        title = config_hourly.iloc[0]['client'] + ' | ' + config_hourly.iloc[0]['experiment']

    layout = {
        'yaxis': {
            'range': [0, 0.5],
            'title': 'CTOR'
        },
        'xaxis': {'showgrid': False},
        'shapes': vlines,
        'title': title,
        'showlegend': True,
        'legend': {'orientation': 'h'},
        'hovermode': 'closest',
        "font": {
            'family': 'Courier New, monospace',
            'size': 14,
            'color': '#7f7f7f'
        },
        'height': 600,
        'annotations': [
            {
                'x': 0.5,
                'y': 1.1,
                'showarrow': False,
                'text': exp_results,
                'xref': 'paper',
                'yref': 'paper'
            }
        ]
    }
    fig = go.Figure(data=data, layout=layout)
    return output_options(output_type, data, fig)


def output_options(output_type, data, fig):
    if output_type == 'notebook':
        plotly.offline.init_notebook_mode()
        plotly.offline.iplot(fig, show_link=False)
        return data
    elif (output_type == 'file' or output_type == 'index'):
        plotly.offline.plot(fig, show_link=False, output_type='file', include_plotlyjs=True)
        return data
    elif output_type == 'div':
        return plotly.offline.plot(fig, show_link=False, output_type='div', include_plotlyjs=False)


def annotate_stop(stop_time):
    return [{
        'type': 'line',
        'x0': stop_time,
        'y0': 0,
        'x1': stop_time,
        'y1': 1,
        'line': {
            'color': 'red',
            'width': 3,
        }
    }]


def annotate_sends(exp_hourly):
    send_hours = exp_hourly[exp_hourly.send].event_time.unique()
    lines = []
    for hour in send_hours:
        line = {
            'type': 'line',
            'x0': pd.Timestamp(hour),
            'y0': 0,
            'x1': pd.Timestamp(hour),
            'y1': 1,
            'line': {
                'color': 'black',
                'width': 1,
            }
        }
        lines.append(line)
    return lines
