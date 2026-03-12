

def classify_shock(patient):
    """
    Determines whether a patient may be in cardiogenic shock.
    """

    if patient["map"] < 65 and patient["lactate"] > 2:
        return True
    else:
        return False


def main():

    patient = {
        "map": 60,
        "lactate": 4.2,
        "cardiac_output": 3.0,
        "urine_output": 20,
        "creatinine": 1.8
    }

    shock = classify_shock(patient)

    print("Cardiogenic shock:", shock)


if __name__ == "__main__":
    main()