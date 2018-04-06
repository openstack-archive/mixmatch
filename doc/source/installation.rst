============
Installation
============

The proxy will be set up in one OpenStack installation, called the Identity
Provider, or IdP, and it redirect API calls to either the local services, or
remote services in one of several Service Provider installations (SP).

Install dependencies. ::

    $ pip install -r requirements.txt
    $ python setup.py install


Web Server
==========
The recommended way is to run the proxy using uwsgi and apache through the
`httpd/mixmatch-uwsgi.ini` and `httpd/mixmatch-uwsgi.conf` files respectively ::

    sudo apt install uwsgi uwsgi-plugin-python libapache2-mod-proxy-uwsgi
    uwsgi mixmatch/httpd/mixmatch-uwsgi.ini
    sudo cp mixmatch/httpd/mixmatch-uwsgi.conf /etc/apache2/sites-available/mixmatch.conf
    sudo a2ensite mixmatch


Running in a Docker Container
=============================
The proxy can be run in a Docker container using the provided Dockerfile.
When it is run, the container port 5001 must be mapped to the port 5001 on the
host and your configuration file must be passed in as a data volume,
for example ::

    sudo docker run \
    --interactive --tty \
    --volume /etc/mixmatch/mixmatch.conf:/<path>/<to>/<local>/mixmatch.conf: \
    --publish 5001:5001 mixmatch

You will still need to edit the configuration file and do the rest of the setup
normally on the host.


Configuration
=============
The proxy searches for the configuration file ``mixmatch.conf`` in the
current directory, the ``etc/mixmatch`` directory relative to the current
directory or ``/etc/mixmatch``.

A sample configuration file has been provided in the ``etc`` folder of the
source code.

The proxy will substitute the endpoint of the service it is proxying.
Only Cinder and Glance are supported for now.

For each SP, you must have an option group in ``mixmatch.conf`` which contains
the service provider name (as it is listed in Keystone's service catalog, but
with the added prefix `sp_`), the URI for connecting to the notification
messagebus in that OpenStack installation, the keystone auth url, and the
endpoints for each of the services enabled under the enabled_services option.
For instance::

    [sp_one]
    sp_name="keystone-sp1"
    messagebus="rabbit://rabbituser:rabbitpassword@192.168.7.20"
    image_endpoint="http://192.168.7.20:9292"
    volume_endpoint="http://192.168.7.20:8776"
    enabled_services=image, volume

You must also have each service provider's name listed under
``service_providers`` in ``[DEFAULT]``.

Keystone Configuration
----------------------

Keystone maintains the service catalog with information about all the
configured endpoints.

In the IdP, delete and then recreate the endpoint which we will proxy. ::

    $ openstack endpoint delete <endpoint_id>
    $ openstack endpoint create \
        --publicurl http://<proxy_host>:<proxy_port>/<service_type>/<api_version> \
        --internalurl http://<proxy_host>:<proxy_port>/<service_type>/<api_version> \
        --adminurl http://<proxy_host>:<proxy_port>/<service_type>/<api_version> \
        --region RegionOne \
        <endpoint_type>

Where service_type is ``image`` if endpoint_type is ``image``
and ``volume`` if endpoint_type is ``volume`` or ``volumev2``

Nova Configuration
------------------

Nova reads the endpoint address for glance from the configuration file stored
in ``/etc/nova/nova.conf``. So, in the IdP, add the following::

    # /etc/nova/nova.conf
    [glance]
    api_servers=<proxy_url>/image

Cinder Notification
-------------------

Cinder reads the endpoint address for glance from the configuration file stored
in ``/etc/cinder/cinder.conf``. So, in the IdP, add the following::

    # /etc/cinder/cinder.conf
    [default]
    glance_api_servers=<proxy_url>/image

Every Cinder must be configured to emit notifications on the messagebus.  So,
in both the IdP and every SP, add the following to
``/etc/cinder/cinder.conf``::

    # /etc/cinder/cinder.conf
    [oslo_messaging_notifications]
    driver = messaging
    topics = notifications
