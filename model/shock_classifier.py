#!/usr/bin/env python3

import logging
import argparse
import socket

format_str = (
    f'[%(asctime)s {socket.gethostname()}] '
    '%(filename)s:%(funcName)s:%(lineno)s - %(levelname)s: %(message)s'
)

parser = argparse.ArgumentParser()
parser.add_argument('-l', '--loglevel',
                    type=str,
                    required=False,
                    default='WARNING',
                    help='set log level to DEBUG, INFO, WARNING, ERROR, or CRITICAL')
args = parser.parse_args()

logging.basicConfig(level=args.loglevel, format=format_str)


def classify_shock(map_val, lactate, cardiac_index, urine_output, creatinine):
    """
    Determines whether a patient is in cardiogenic shock.
    Shock is flagged when hemodynamic compromise (low MAP) is present
    alongside at least one marker of end-organ hypoperfusion.

    Args:
        map_val (float):       Mean arterial pressure (mmHg)
        lactate (float):       Serum lactate (mmol/L)
        cardiac_index (float): Cardiac index (L/min/m^2)
        urine_output (float):  Urine output (mL/hr)
        creatinine (float):    Serum creatinine (mg/dL)

    Returns:
        bool: True if patient meets criteria for cardiogenic shock
    """
    logging.info(f'Classifying shock with MAP={map_val}, lactate={lactate}, '
                 f'cardiac_index={cardiac_index}, urine_output={urine_output}, '
                 f'creatinine={creatinine}')

    hemodynamic_compromise = map_val <= 60
    logging.debug(f'Hemodynamic compromise (MAP <= 60): {hemodynamic_compromise}')

    hypoperfusion_count = 0
    if lactate >= 2.0:
        hypoperfusion_count += 1
        logging.debug(f'Lactate {lactate} >= 2.0: hypoperfusion marker present')
    if cardiac_index < 2.2:
        hypoperfusion_count += 1
        logging.debug(f'Cardiac index {cardiac_index} < 2.2: hypoperfusion marker present')
    if urine_output < 30:
        hypoperfusion_count += 1
        logging.debug(f'Urine output {urine_output} < 30: hypoperfusion marker present')
    if creatinine > 1.5:
        hypoperfusion_count += 1
        logging.debug(f'Creatinine {creatinine} > 1.5: hypoperfusion marker present')

    logging.info(f'Hypoperfusion markers met: {hypoperfusion_count}')

    result = hemodynamic_compromise and hypoperfusion_count >= 1
    logging.info(f'Cardiogenic shock classification result: {result}')

    return result


def main():
    try:
        shock = classify_shock(
            map_val=60,
            lactate=4.2,
            urine_output=20,
            creatinine=1.8,
            cardiac_index=1.9,
        )
        print(f'Cardiogenic Shock: {shock}')

    except Exception as e:
        logging.error(f'Error: {e}')


if __name__ == '__main__':
    main()