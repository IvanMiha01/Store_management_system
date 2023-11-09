FROM python:3

COPY ./configuration.py /configuration.py
COPY ./models.py /models.py
COPY ./decorators.py /decorators.py
COPY ./owner.py /owner.py
COPY ./requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

ENTRYPOINT [ "python", "owner.py" ]