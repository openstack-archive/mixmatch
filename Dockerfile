# Usage example:

# docker build -t mixmatch .

# sudo docker run \
# --interactive --tty \
# --volume /etc/mixmatch/mixmatch.conf:/etc/mixmatch/mixmatch.conf \
# --publish 5001:5001 mixmatch

# Make sure that all localhost/127.0.0.1 references in the config are replaced
# with the IP of the idp and that it is configured correctly otherwise

FROM python:3-onbuild

RUN pip install uwsgi

EXPOSE 5001
CMD ["bash", "/usr/src/app/run_proxy.sh"]
