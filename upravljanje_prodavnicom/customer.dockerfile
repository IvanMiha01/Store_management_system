FROM python:3

COPY ./configuration.py /configuration.py
COPY ./models.py /models.py
COPY ./decorators.py /decorators.py
COPY ./customer.py /customer.py

COPY ./OrderContract.abi ./OrderContract.abi
COPY ./OrderContract.bin ./OrderContract.bin
COPY ./OrderContract.sol ./OrderContract.sol

COPY ./requirements.txt /requirements.txt


RUN pip install -r /requirements.txt

ENTRYPOINT [ "python", "customer.py" ]