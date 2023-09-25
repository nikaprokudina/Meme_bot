FROM python:3.10

RUN apt-get -y update && apt-get install -y \
    python3-dev \
    python3-pip \
    python3-setuptools \
    libpq-dev

RUN pip install --upgrade pip

WORKDIR /app

COPY requirements.txt ./

RUN python3 -m pip install -r requirements.txt --no-cache-dir

COPY . .