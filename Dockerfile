# LETS BUILD A DOCKER IMAGE
FROM ubuntu:latest

WORKDIR /microqr

COPY . .

RUN apt-get update \
    && apt-get install --assume-yes --no-install-recommends --quiet \
        python3 \
        python3-pip \
    && apt-get clean all && \
    apt-get install -y default-jre && \
    apt-get install -y libgl1-mesa-glx libglib2.0-0 &&  \
    rm -rf /var/lib/apt/lists/*


COPY requirements.txt .

# Update pip
#RUN pip3 install --upgrade pip

RUN pip3 install -r requirements.txt


CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

EXPOSE 5000
