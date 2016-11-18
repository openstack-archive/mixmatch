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
The recommended way is to run the proxy using uWSGI through the
``run_proxy.sh`` script. ::

    $ ./run_proxy.sh


It is also possible to run the proxy with Apache2 and ``mod_wsgi``, but there
are limitations compared to running it with uWSGI.

- Image uploading with Glance doesn't work unless running Apache in embedded
  mode.
- Image API v1 uses underscores in the header keys, which are silently dropped
  by Apache. Hacking the configuration to allow these through is required.

To run the proxy with Apache in Ubuntu: ::

    $ apt-get install libapache2-mod-wsgi
    $ cp httpd/apache.conf /etc/apache2/sites-available/proxy.conf
    $ cp etc/k2k-proxy.conf /etc/
    $ a2ensite proxy
    $ service apache2 reload


Configuration
=============
The proxy searches for the configuration file ``k2k-proxy.conf`` in the
current directory, the ``etc/`` directory relative to the current directory or
``/etc/``

A sample configuration file has been provided in the ``etc`` folder of the
source code.

The proxy will substitute the endpoint of the service it is proxying.
Only Cinder and Glance are supported for now.

For each SP, you must have a section in ``k2k-proxy.conf`` which contains the
service provider name (as it is listed in Keystone's service catalog), and the
URI for connecting to the notification messagebus in that OpenStack
installation.  For instance::

    [sp_one]
    sp_name="keystone-sp1"
    messagebus="rabbit://rabbituser:rabbitpassword@192.168.7.20"
    image_endpoint="http://192.168.7.20:9292"
    volume_endpoint="http://192.168.7.20:8776"

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

