# Build:
#    sudo docker build -t mixmatch .
# Run the container:
#   sudo docker run -t
#    --volume /<path>/<to>/<local>/mixmatch.conf:/etc/mixmatch/mixmatch.conf:ro
#    --publish 5001:5001 mixmatch

FROM python:3-onbuild
RUN pip install uwsgi
WORKDIR /usr/app/src/mixmatch
COPY . /usr/app/src/mixmatch
RUN pip install -r /usr/app/src/mixmatch/requirements.txt
RUN pip install /usr/app/src/mixmatch
EXPOSE 5001
CMD /usr/local/bin/uwsgi --ini /usr/app/src/mixmatch/httpd/mixmatch-uwsgi.ini
