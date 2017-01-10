================================
Authentication and Authorization
================================

To perform authentication between service providers, mixmatch uses
Keystone-to-Keystone. This feature allows federation of identities between
OpenStack deployments.

For more information on Keystone-to-Keystone federation please visit the
Keystone documentation_. The rest of this page will assume that you have
already set up federation.

.. _documentation: http://docs.openstack.org/developer/keystone/federation/federated_identity.html

Mappings
========

When a SAML2 assertion is presented to Keystone from the user, Keystone will
use the attributes in the assertion to determine the user credentials and
level of authorization to grant to the user. This is done through mappings_.

.. _mappings: http://docs.openstack.org/developer/keystone/federation/mapping_combinations.html

For our reference architecture, where a user is mapped to a project of the
same name as the project where the user is coming from we provide the
following mapping which can be modified based on requirements: ::

    [
        {
            "local": [
                {
                    "user": {
                        "name": "{0}"
                    },
                    "group": {
                        "name": "{1}",
                        "domain": { "id": "default" }
                    }
                }
            ],
            "remote": [
                {
                    "type": "openstack_user"
                },
                {
                    "type": "openstack_project"
                },
                {
                    "type": "openstack_user",
                    "not_any_of": [
                      "admin",
                      "nova",
                      "cinder",
                      "glance",
                      "neutron"
                    ]
                }
            ]
        }
    ]


This mapping will map to a user with the same username but part of the
federated domain, and upon authentication will make the user part of a
group named the same as the project the user is coming from. The group
must be explicitly created ahead of time and granted permission to the
respective local project.
