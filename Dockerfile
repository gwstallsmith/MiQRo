# LETS BUILD A DOCKER IMAGE
FROM python:3.9-slim-buster

# Install system dependencies
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx libglib2.0-0 &&  \
    rm -rf /var/lib/apt/lists/*

WORKDIR /microqr

COPY requirements.txt .

# Update pip
RUN pip3 install --upgrade pip

RUN pip3 install -r requirements.txt

COPY . .

CMD ["flask", "run", "--host=0.0.0.0"]

EXPOSE 5000