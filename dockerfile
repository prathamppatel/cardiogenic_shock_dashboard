FROM python:3.12

COPY shock_classifier.py /code/shock_classifier.py

ENV PATH="/code:$PATH"