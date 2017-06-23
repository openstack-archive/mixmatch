===================
Developer Reference
===================

The Mixmatch project is generously hosted by the OpenStack infrastructure.
While the project is funded and developed primarily by the Massachusetts Open
Cloud, we are always welcoming to new contributors.

Contributing to OpenStack
=========================

.. include:: ../../CONTRIBUTING.rst

Setting up a development environment
====================================

Devstack is the mechanism of choice for setting up a development environment.
For the latest branch we recommend a virtual machine running Ubuntu 16.04, with
more than 4GB of RAM and 40GB of space.

Clone Devstack from git (#1) and copy the sample configuration file from the
samples folder to the root folder (#2). Next, open the newly copied
`local.conf` file with your editor of choice (in our case `vi` #3).::

    git clone git://git.openstack.org/openstack-dev/devstack #1
    cd devstack
    cp samples/local.conf . #2
    vi local.conf #3

Devstack is extensible and allows plugins for the installation and
configuration of different additional components depending on need. Mixmatch
provides one such Devstack plugin, so let's go ahead an enable it by adding
the following line at the end of `local.conf`. ::

    enable_plugin mixmatch git://git.openstack.org/openstack/mixmatch
    REGISTER_MIXMATCH=true

Finally, run `stack.sh`. (We recommend doing so inside a screen in case of
connectivity issues.) This should take around 20-30 minutes and is a good time
to brew some coffee. ::

    ./stack.sh

Running the tests
=================

There are two types of tests. Unit tests and functional tests. These are run
automatically on every proposed change.

Unit tests
----------

Unit tests do not require setting up a development environment and can be
simply run through `tox`. `tox` can be installed through pip (#1) or from the
system packages (#2, #3). ::

    sudo pip install tox #1
    sudo apt install python-tox #2
    sudo yum install python-tox #3

`tox` supports multiple testing environments, and a specific one can be
selected by running `tox -e <environment>`. Valid environment choices are
`py27`, `py35`, and `pep8`. For example, to run the unit tests in the
Python 2.7 environment: ::

    tox -e py27

The `pep8` environment will not run the unit tests, but will check the code
for conformance to the PEP8 coding guidelines for Python.

Passing the checks for all the above three environments is a hard requirement
for the approval of proposed changes.

Functional tests
----------------

While unit tests do not require a development environment, functional tests do.
See above for how to set up one.

Functional testing is done through tempest. It exercises the proxying
functionality by running all the API tests for the Compute, Volume, and Image
services. Additionally it runs all the scenario tests which simulate a
more realistic workload. We maintain a blacklist file in
`mixmatch/tests/functioanl/tempest_blacklist.txt` for individual tests which
fail for known reasons. To run the functional tests, change into the tempest
directory (#1) and run #2: ::

    cd /opt/stack/tempest #1
    ostestr -r '(^tempest.api.compute|^tempest.api.image|^tempest.api.volume|^tempest.scenario)' \
        --blacklist-file <MIXMATCH_DIR>/mixmatch/mixmatch/tests/functional/tempest_blacklist.txt #2