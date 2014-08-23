Best Practice
=============

Offline Runqueue
----------------

Suppose you have set the offline runner user in ``config.py``,
for example ``railgun-offline``, you may prevent the runner
from accessing public network via `iptables`:

.. code-block:: bash

    sudo iptables -A OUTPUT -m owner --uid-owner railgun-offline -d 127.0.0.1 -j ACCEPT
    sudo iptables -A OUTPUT -m owner --uid-owner railgun-offline -j DROP

If your website and your runner is installed on seperate machine, for example
``192.168.1.101`` as your website and ``192.168.1.102`` as your runner,
you may add another rule to allow the runner accessing the website API:

.. code-block:: bash

    sudo iptables -A OUTPUT -m owner --uid-owner railgun-offline -d 127.0.0.1 -j ACCEPT
    sudo iptables -A OUTPUT -m owner --uid-owner railgun-offline -d 192.168.1.101 -j ACCEPT
    sudo iptables -A OUTPUT -m owner --uid-owner railgun-offline -j DROP

You may need to add your website domain into ``/etc/hosts``, because the above
commands forbid DNS requests as well.

It is recommended to install the runner on a seperate machine, in that you can
forbid most services except the Redis server.  You may do this by the following
`iptables` configuration:

.. code-block:: bash

    sudo iptables -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
    sudo iptables -A INPUT -i eth0 -p icmp -m icmp --icmp-type 8 -j ACCEPT
    sudo iptables -A INPUT -i eth0 -p tcp -m tcp --dport 22 -j ACCEPT
    sudo iptables -A INPUT -i eth0 -p tcp -m tcp --dport 6379 -j ACCEPT
    sudo iptables -A INPUT -i eth0 -j DROP

After executing the above commands, the machine will only respond to ICMP ping
requests, SSH remote login, and Redis connections from outside.

