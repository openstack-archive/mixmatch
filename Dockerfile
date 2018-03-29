# Build:
#    sudo docker build -t mixmatch .
# Run the container:
#    sudo docker run -d -t mixmatch
FROM ubuntu:16.04
RUN apt-get update
RUN apt-get -y install python
RUN apt-get -y install python-pip
RUN apt-get -y install git
RUN pip install uwsgi
WORKDIR /usr/app/src/
RUN git clone https://github.com/openstack/mixmatch.git
RUN pip install -r /usr/app/src/mixmatch/requirements.txt
RUN pip install /usr/app/src/mixmatch
EXPOSE 5001
CMD /usr/local/bin/uwsgi --ini /usr/app/src/mixmatch/httpd/mixmatch-uwsgi.ini
