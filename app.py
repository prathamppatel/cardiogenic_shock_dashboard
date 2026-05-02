#!/usr/bin/env python3

import argparse
import json
import logging
import socket
import pickle
import redis
import pandas as pd
import dash_bootstrap_components as dbc
from dash import Dash, Input, Output, State, callback, dash_table, html


format_str = (
    f'[%(asctime)s {socket.gethostname()}] '
    '%(filename)s:%(funcName)s:%(lineno)s - %(levelname)s: %(message)s'
)

parser = argparse.ArgumentParser(description='Cardiogenic Shock Classifier Dashboard')
parser.add_argument('-l', '--loglevel',
                    type=str,
                    required=False,
                    default='WARNING',
                    help='set log level to DEBUG, INFO, WARNING, ERROR, or CRITICAL')
parser.add_argument('--host',
                    type=str,
                    required=False,
                    default='0.0.0.0',
                    help='host address for the Dash server (default: 0.0.0.0)')
parser.add_argument('--port',
                    type=int,
                    required=False,
                    default=8050,
                    help='port for the Dash server (default: 8050)')
parser.add_argument('--debug',
                    action='store_true',
                    help='run Dash server in debug mode')
args = parser.parse_args()

logging.basicConfig(level=args.loglevel, format=format_str)


with open('model/scai_classifier.pkl', 'rb') as f:
    scai_model = pickle.load(f)

rd = redis.Redis(host='redis', port=6379, db=0)

app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server


app.layout = dbc.Container([

    dbc.Row([
        html.H2("Cardiogenic Shock Classifier",
                className="text-center text-primary mt-4 mb-4")
    ]),

    dbc.Card([
        dbc.CardBody([
            html.H5("Patient Vitals", className="card-title mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("MAP (mmHg)"),
                    dbc.Input(id='input-map', type='number',
                              placeholder='e.g. 60', min=0, max=200),
                ], width=4),
                dbc.Col([
                    dbc.Label("Lactate (mmol/L)"),
                    dbc.Input(id='input-lactate', type='number',
                              placeholder='e.g. 4.2', min=0, max=30),
                ], width=4),
                dbc.Col([
                    dbc.Label("Cardiac Index (L/min/m^2)"),
                    dbc.Input(id='input-ci', type='number',
                              placeholder='e.g. 1.9', min=0, max=10),
                ], width=4),
            ], className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Urine Output (mL/hr)"),
                    dbc.Input(id='input-uo', type='number',
                              placeholder='e.g. 20', min=0, max=500),
                ], width=4),
                dbc.Col([
                    dbc.Label("Creatinine (mg/dL)"),
                    dbc.Input(id='input-creatinine', type='number',
                              placeholder='e.g. 1.8', min=0, max=20),
                ], width=4),
            ], className="mb-3"),

            dbc.Button("Classify Patient", id='submit-button',
                       color="primary", className="mt-2"),
        ])
    ], className="mb-4"),

    html.Div(id='result-banner', className="mb-4"),

    dbc.Card([
        dbc.CardBody([
            html.H5("Patient Database", className="card-title mb-3"),
            html.Div(id='patient-table')
        ])
    ]),

], fluid=True)

def classify_shock(map_val, lactate, urine_output, creatinine, cardiac_index):
    """
    Determines whether a patient is in cardiogenic shock.
    Shock is flagged when hemodynamic compromise (low MAP) is present
    alongside at least one marker of end-organ hypoperfusion.

    Args:
        map_val (float):       Mean arterial pressure (mmHg)
        lactate (float):       Serum lactate (mmol/L)
        urine_output (float):  Urine output (mL/hr)
        creatinine (float):    Serum creatinine (mg/dL)
        cardiac_index (float): Cardiac index (L/min/m²)

    Returns:
        bool: True if patient meets criteria for cardiogenic shock
    """
    ci = cardiac_index
    hemodynamic_compromise = map_val <= 60

    hypoperfusion_count = 0
    if lactate >= 2.0:
        hypoperfusion_count += 1
    if ci < 2.2:
        hypoperfusion_count += 1
    if urine_output < 30:
        hypoperfusion_count += 1
    if creatinine > 1.5:
        hypoperfusion_count += 1

    result = hemodynamic_compromise and hypoperfusion_count >= 1
    logging.debug(f'classify_shock: MAP={map_val} CI={ci} hypoperfusion_count={hypoperfusion_count} result={result}')
    return result


def build_table():
    """
    Reads all patient entries from Redis and builds a Dash DataTable.

    Returns:
        dash_table.DataTable: Table of all stored patients, or a
                              placeholder message if none exist.
    """
    keys = rd.keys('patient:*')
    logging.debug(f'build_table: found {len(keys)} patient keys in Redis')

    if not keys:
        return html.P("No patients recorded yet.", className="text-muted")

    rows = []
    for key in keys:
        patient = json.loads(rd.get(key))
        rows.append({
            'Patient ID':    patient['id'],
            'MAP (mmHg)':    patient['map'],
            'Lactate':       patient['lactate'],
            'Cardiac Index': patient['ci'],
            'Urine Output':  patient['urine_output'],
            'Creatinine':    patient['creatinine'],
            'Shock':         'Yes' if patient['shock'] else 'No',
            'SCAI Stage':    patient.get('scai_stage', 'N/A')
        })

    columns = [
        {'name': 'Patient ID',    'id': 'Patient ID'},
        {'name': 'MAP (mmHg)',    'id': 'MAP (mmHg)'},
        {'name': 'Lactate',       'id': 'Lactate'},
        {'name': 'Cardiac Index', 'id': 'Cardiac Index'},
        {'name': 'Urine Output',  'id': 'Urine Output'},
        {'name': 'Creatinine',    'id': 'Creatinine'},
        {'name': 'Shock',         'id': 'Shock'},
        {'name': 'SCAI Stage',    'id': 'SCAI Stage'}
    ]

    return dash_table.DataTable(
        data=rows,
        columns=columns,
        style_header={
            'backgroundColor': '#375a7f',
            'color':           'white',
            'fontWeight':      'bold'
        },
        style_data={
            'backgroundColor': '#303030',
            'color':           'white'
        },
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{Shock} = "Yes"',
                    'column_id': 'Shock'
                },
                'color': '#e74c3c',
                'fontWeight': 'bold'
            },
            {
                'if': {
                    'filter_query': '{Shock} = "No"',
                    'column_id': 'Shock'
                },
                'color': '#2ecc71',
                'fontWeight': 'bold'
            }
        ],
        style_table={'overflowX': 'auto'},
        page_size=10
    )


@callback(
    Output('result-banner', 'children'),
    Output('patient-table', 'children'),
    Input('submit-button', 'n_clicks'),
    State('input-map', 'value'),
    State('input-lactate', 'value'),
    State('input-ci', 'value'),
    State('input-uo', 'value'),
    State('input-creatinine', 'value'),
    prevent_initial_call=True
)
def classify_and_store(n_clicks, map_val, lactate, ci, uo, creatinine):
    """
    Classifies the patient on button click, stores result in Redis,
    and updates the result banner and patient table.

    Args:
        n_clicks (int):     Number of times submit button has been clicked
        map_val (float):    Mean arterial pressure (mmHg)
        lactate (float):    Serum lactate (mmol/L)
        ci (float):         Cardiac index (L/min/m²)
        uo (float):         Urine output (mL/hr)
        creatinine (float): Serum creatinine (mg/dL)

    Returns:
        tuple: (result banner component, patient table component)
    """
    if map_val is None or lactate is None or ci is None or uo is None or creatinine is None:
        logging.warning(f'classify_and_store: one or more fields are missing')
        banner = dbc.Alert("Please fill in all fields before classifying.",
                           color="warning")
        return banner, build_table()

    logging.info(f'classify_and_store: MAP={map_val} lactate={lactate} CI={ci} UO={uo} creatinine={creatinine}')

    shock = classify_shock(map_val, lactate, uo, creatinine, ci)

    input_df = pd.DataFrame([{
        'map':           map_val,
        'lactate':       lactate,
        'cardiac_index': ci,
        'urine_output':  uo,
        'creatinine':    creatinine
    }])
    scai_prediction = scai_model.predict(input_df)[0]
    logging.info(f'classify_and_store: shock={shock} SCAI stage={scai_prediction}')

    patient_id = rd.incr('patient_count')
    patient_data = {
        'id':           patient_id,
        'map':          map_val,
        'lactate':      lactate,
        'ci':           ci,
        'urine_output': uo,
        'creatinine':   creatinine,
        'shock':        shock,
        'scai_stage':   scai_prediction
    }
    rd.set(f'patient:{patient_id}', json.dumps(patient_data))
    logging.debug(f'classify_and_store: stored patient {patient_id} in Redis')

    banner_text = f"Result: {'SHOCK' if shock else 'NO SHOCK'} | SCAI Stage: {scai_prediction}"
    banner = dbc.Alert(banner_text, color="danger" if shock else "success",
                       className="text-center fs-5 fw-bold")

    return banner, build_table()


def main():
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()