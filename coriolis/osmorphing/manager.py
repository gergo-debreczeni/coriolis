from oslo_log import log as logging
import paramiko

from coriolis.osmorphing import factory as osmorphing_factory
from coriolis.osmorphing.osmount import factory as osmount_factory
from coriolis import utils

LOG = logging.getLogger(__name__)


def morph_image(connection_info, target_hypervisor, target_platform,
                volume_devs, nics_info, event_manager):
    (ip, port, username, pkey) = connection_info

    LOG.info("Waiting for connectivity on host: %(ip)s:%(port)s",
             {"ip": ip, "port": port})
    utils.wait_for_port_connectivity(ip, port)

    event_manager.progress_update(
        "Connecting to host: %(ip)s:%(port)s" % {"ip": ip, "port": port})
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=ip, port=port, username=username, pkey=pkey)

    os_mount_tools = osmount_factory.get_os_mount_tools(ssh, event_manager)

    event_manager.progress_update("Discovering and mounting OS partitions")
    os_root_dir, other_mounted_dirs = os_mount_tools.mount_os(volume_devs)
    os_morphing_tools, os_info = osmorphing_factory.get_os_morphing_tools(
        ssh, os_root_dir, target_hypervisor, target_platform, event_manager)

    event_manager.progress_update('OS being migrated: %s' % str(os_info))

    os_morphing_tools.set_net_config(nics_info, dhcp=True)
    LOG.info("Pre packages")
    os_morphing_tools.pre_packages_install()

    (packages_add,
     packages_remove) = os_morphing_tools.get_packages()

    if packages_add:
        event_manager.progress_update(
            "Adding packages: %s" % str(packages_add))
        os_morphing_tools.install_packages(packages_add)

    if packages_remove:
        event_manager.progress_update(
            "Removing packages: %s" % str(packages_remove))
        os_morphing_tools.uninstall_packages(packages_remove)

    LOG.info("Post packages")
    os_morphing_tools.post_packages_install()

    event_manager.progress_update("Dismounting OS partitions")
    os_mount_tools.dismount_os(other_mounted_dirs + [os_root_dir])
