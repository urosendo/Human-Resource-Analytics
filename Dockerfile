FROM python:3.8-slim-buster

RUN mkdir -p /home/project
WORKDIR /home/project

RUN pip install --upgrade pip
RUN pip install jupyter notebook 

EXPOSE 8888

ENTRYPOINT [ "jupyter", "notebook", "--ip=0.0.0.0", "--allow-root", "--no-browser"]