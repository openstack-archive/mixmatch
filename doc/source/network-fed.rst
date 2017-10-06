==================
Network Federation
==================

What is meant by "network federation"?
======================================
Mixmatch offers a mechanism to extend a network across clouds. Note that this
idea of 'extending' is different than the direct access which the image
federation and volume federation features offer. A user's choice to extend a
network will usually be explicit and voluntary, whereas the sharing of images
and volumes tends towards being implicit and automatic.

Support for network federation requires that Neutron be backed by the ML2
plugin. This plugin is often considered normal, or vanilla, so most clouds
probably satisfy this requirement easily.

The precise mechanism which allows the network federation feature to function
is VXLAN tunneling between clouds.

Finally, note that currently the scope of this feature is limited to extending
networks from a remote cloud to the so-called 'local' cloud in which the
Mixmatch proxy service resides.

Network federation for operators
================================
Some steps must be taken to configure clouds in such a way that the network
federation feature works as intended.

Registering remote VXLAN endpoints
----------------------------------
In a single-cloud deployment, the Neutron ML2 plugin creates a VXLAN mesh
among compute nodes, to allow virtual machines residing on separate physical
hardware to communicate.

The ability to manipulate the VXLAN mesh is not exposed by the Neutron API, so
operators must edit database entries manually. Below, we use MySQL as an
example, but operators should take care to translate these queries to be
compatibile with their own database.

Below is how the database entries may appear for a single-cloud deployment:

.. sourcecode:: console

    mysql> select * from neutron.ml2_vxlan_endpoints;
    +-------------+----------+------------+
    | ip_address  | udp_port | host       |
    +-------------+----------+------------+
    | 10.19.97.20 |     4789 | compute-01 |
    | 10.19.97.21 |     4789 | controller |
    | 10.19.97.22 |     4789 | compute-02 |
    +-------------+----------+------------+
    3 rows in set (0.00 sec)
..

These entries are automatically populated by Neutron and contain references to
each compute node in the cloud.

In order to allow networks to extend across clouds, operators should simply
insert entries for the compute nodes in remote clouds:

.. sourcecode:: console

    mysql> insert into neutron.ml2_vxlan_endpoints (ip_address, udp_port, host) values ('129.10.5.10', 4789, 'compute-01.remotecloud.org');
    Query OK, 1 row affected (0.00 sec)

    mysql> select * from neutron.ml2_vxlan_endpoints;
    +-------------+----------+----------------------------+
    | ip_address  | udp_port | host                       |
    +-------------+----------+----------------------------+
    | 10.19.97.20 |     4789 |                 compute-01 |
    | 10.19.97.21 |     4789 |                 controller |
    | 10.19.97.22 |     4789 |                 compute-02 |
    | 129.10.5.10 |     4789 | compute-01.remotecloud.org |
    +-------------+----------+----------------------------+
    4 rows in set (0.00 sec)
..

Finally, operators should take care to ensure that the incoming UDP traffic on
port 4789 is in-fact permitted.

**NOTE**: Similar steps to those above must be performed on each cloud, in
order to support bidirectional traffic.

Because managing numerous entries in the database can become unwieldy, an
operator might consider installing some device, of an unknown nature, which
could perform VXLAN termination for an entire cloud. A reference to this
device would appear in the database instead of entries for each compute node.

Configuring Neutron policies
----------------------------
The operations which Mixmatch performs to extend a network are, by default and
by nature, privileged operations. The default Neutron policy restricts the
performance of these operations to users with the ``admin`` role. Therefore, in
its home cloud only the Mixmatch service user should have this role.

In a federation of clouds, however, the landlord of each remote cloud will
probably not want to give out this ``admin`` role. In fact he or she will want
to only give the Mixmatch service user the minimal amount of elevated
permissions needed to perform the network-extending operations, and no more.

Therefore a new role, which we will call ``mixmatch_fancy_role``, should be
created in each remote cloud. Operators should ensure that the Mixmatch service
user is given this role in its mapped projects in those remote clouds. Then,
the following entries in the Neutron ``policy.json`` file should be changed or
added: (at the time of writing Neutron still does not have any default policies
registered in code, so the rest of the policy file must stay intact)

.. sourcecode:: json

    {
        "mixmatch": "role:mixmatch_fancy_role",
        "context_is_advsvc": "rule:mixmatch",

        "get_network:provider:segmentation_id": "rule:admin_only or rule:mixmatch"
    }
..

Note that due to limitations in Neutron's policy engine we must take advantage
of the ``advsvc`` ("Advanced Services") permission feature, rather than define
our own custom policy. Therefore, operators might want to additionally tweak
the other default entries in policy.json which reference this role (mostly
related to port operations).

Ensuring non-conflicting VXLAN IDs
----------------------------------
Because Mixmatch will be creating new networks with a particular VXLAN ID
specified, there may be conflicts if the various remote clouds assign these
IDs randomly (the default behavior). In the
``/etc/neutron/plugins/ml2/ml2_conf.ini`` file of each cloud, operators should
take care to set a reasonable and non-overlapping ``start:end`` value for
``[ml2_type_vxlan]/vni_ranges``.

Network federation for users
============================
Users consume the network federation feature by sending requests to an
extension of the Neutron API which is exposed by the Mixmatch proxy service.

API reference
-------------
The details of that API call follow below. (Note that because the network
extending is always performed as remote-to-local, the ``MM-SERVICE-PROVIDER``
header is not understood by this call.)

.. sourcecode:: console

    POST <mixmatch url>/network/v2.0/networks/extended
..

.. sourcecode:: json

    {
        "network": {
            "existing_net_id": "60ed86b2-8db8-4459-8d31-475345534dec",
            "existing_net_sp": "some_remote_sp",
            "name": "my_cool_extended_network"
        }
    }
..

On success, the response of this API call will be identical in format to the
standard Neutron POST ``/v2.0/networks``. On failure, there are several
specific error codes which can be returned:

* 400, if ``existing_net_id`` or ``existing_net_sp`` are not present in the
  request body
* 401, if the user is unauthorized (no token or invalid token)
* 403, if the user is not the owner of the network which they wish to extend
* 409, if there is a naming conflict for the extended network
* 422, if a request to Neutron ended with a client-side error (usually network
  not found), or if the service provider is not known to Mixmatch
* 503, if a request to Neutron ended with a server-side error

Subnet management
-----------------
Note however, that it will remain the responsibility of the user to manage
the subnets of extended networks. In other words, the network-extending
functionality which Mixmatch exposes does not perform any subnet operations.

Users should take care to make sure that for the subnet in each cloud, the
first three octets of the (IPv4) subnet are the same, but that the allocation
pools do not overlap. Additionally, the user should ensure that DHCP is only
enabled for the subnet of one cloud and not the other. (The choice of which
subnet will offer DHCP can, in practice, be an arbitrary one.) Users can have
the two subnets share one router ("gateway"), or have a separate gateway for
each cloud.

Some example code which may help in following these guidelines is found below:

.. sourcecode:: console

    old_subnet = (
        [s for s in CLOUD1_NEUTRON_CLIENT.list_subnets()['subnets']
         if (s['ip_version'] == 4 and
             s['network_id'] == CLOUD1_NETWORK_ID)][0]
    )
    old_subnet_id = old_subnet['id']
    old_subnet_start = old_subnet['allocation_pools'][0]['start']
    maximum_ip = int(
        old_subnet['allocation_pools'][0]['end']
        .split('.')[-1]
    )
    pool_base = re.sub(r'\d+$', '', old_subnet_start)
    CLOUD1_NEUTRON_CLIENT.update_subnet(
        old_subnet_id, body={'subnet': {'allocation_pools':
                             [{'start': old_subnet_start,
                               'end': '{}{}'.format(
                                   pool_base, maximum_ip // 2)}]}}
    )
    new_subnet_body = (
        {'enable_dhcp': False,
         'network_id': CLOUD2_NETWORK_ID,
         'dns_nameservers': old_subnet['dns_nameservers'],
         'ip_version': 4,
         'gateway_ip': old_subnet['gateway_ip'],
         'cidr': old_subnet['cidr'],
         'allocation_pools':
         [{'start': '{}{}'.format(pool_base, maximum_ip // 2 + 1),
           'end': '{}{}'.format(pool_base, maximum_ip)}]
         }
    )
    new_subnet = CLOUD2_NEUTRON_CLIENT.create_subnet(
        body={'subnet': new_subnet_body})
..
