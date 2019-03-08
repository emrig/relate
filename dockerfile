# Use an official Python runtime as a parent image
FROM python:3.7-alpine as workerbase

# Get Java and other packages via the package manager
# --no-cache
RUN apk update \
&& apk upgrade \
&& apk add bash \
&& apk add --virtual=build-dependencies unzip \
&& apk add curl \
&& apk add unzip \
&& apk add openjdk8-jre

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN apk add postgresql-dev gcc python3-dev musl-dev
RUN pip install --upgrade setuptools
#RUN pip install --trusted-host pypi.python.org -r requirements.txt


## pipenv
RUN pip install pipenv
COPY Pipfile Pipfile.lock /app/
RUN pipenv install --dev --system --deploy

ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk
ENV PATH $JAVA_HOME/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Get Stanford NER model
RUN mkdir -p models
RUN curl -sS https://nlp.stanford.edu/software/stanford-ner-2018-10-16.zip > stanford-ner-2018-10-16.zip
RUN unzip -o stanford-ner-2018-10-16.zip -d models

# Make port 80 available to the world outside this container
EXPOSE 80

# Run workertest.py when the container launches
#CMD ["python", "manage.py"]
