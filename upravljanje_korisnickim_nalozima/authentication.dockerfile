FROM python:3

COPY ./configuration.py /configuration.py
COPY ./models.py /models.py
COPY ./app.py /app.py
COPY ./requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

ENTRYPOINT [ "python", "app.py" ]