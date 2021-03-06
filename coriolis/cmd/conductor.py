import eventlet
eventlet.monkey_patch()

import sys

from oslo_config import cfg

from coriolis.conductor.rpc import server as rpc_server
from coriolis import service
from coriolis import utils

CONF = cfg.CONF


def main():
    utils.setup_logging()
    CONF(sys.argv[1:], project='coriolis',
         version="1.0.0")

    launcher = service.get_process_launcher()
    server = service.MessagingService(
        'coriolis_conductor', [rpc_server.ConductorServerEndpoint()],
        rpc_server.VERSION)
    launcher.launch_service(server, workers=server.get_workers_count())
    launcher.wait()


if __name__ == "__main__":
    main()
