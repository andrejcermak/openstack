from keystoneauth1 import session
from keystoneauth1.identity.v3 import OidcAccessToken, Token
import datetime, time
import yaml
from openstack import connection
from oslo_utils import encodeutils
import os
import base64
from requests import put, get
from openstack.compute.v2 import server, flavor, image

class VirtualMachineHandler:

    def create_connection(self):
        try:
            admin = OidcAccessToken(auth_url=self.AUTH_URL,
                                    identity_provider=self.IDENTITY_PROVIDER,
                                    protocol=self.PROTOCOL,
                                    access_token=self.ACCESS_TOKEN)

            sess = session.Session(auth=admin)
            conn = connection.Connection(session=sess)

            unscoped_token = conn.authorize()
            user_id = admin.get_user_id(sess)

            projects = get("https://identity.cloud.muni.cz/v3/users/%s/projects" % user_id,
                      headers={"Accept": "application/json",
                               "User-Agent": "Mozilla/5.0 (X11;",
                               "X-Auth-Token": unscoped_token}).json()['projects']
            if projects:
                self.PROJECT_ID = projects[0]["id"]
                self.PROJECT_DOMAIN_ID = projects[0]["domain_id"]

            t = Token(auth_url=self.AUTH_URL,
                      token=unscoped_token,
                      project_domain_id=self.PROJECT_DOMAIN_ID,
                      project_id=self.PROJECT_ID)

            sess = session.Session(auth=t)
            conn = connection.Connection(session=sess)

        except Exception as e:
            # raise Exception('Client failed authentication at Openstack Reason: {}'.format(e))
            self.STATUS = 'Client failed authentication at Openstack Reason: {}'.format(e)
            return None
        self.SESSION = sess
        return conn

    def __init__(self, access_token):
        self.AUTH_URL = "https://identity.cloud.muni.cz/v3"
        self.ACCESS_TOKEN = access_token
        self.IDENTITY_PROVIDER = "login.cesnet.cz"
        self.PROTOCOL = "openid"
        self.NETWORK = None
        self.SESSION = None
        self.PROJECT_DOMAIN_ID = None
        self.PROJECT_ID = None
        self.STATUS = None
        self.conn = self.create_connection()
'''
    def list_default(self, function):
        try:
            tmp = function

        except Exception as e:
            return
        return [r for r in tmp]

    def list_networks(self):
        return self.list_default(self.conn.network.networks())

    def list_images(self):
        return self.list_default(self.conn.image.images())

    def list_flavors(self):
        return self.list_default(self.conn.compute.flavors())

    def list_security_groups(self):
        return self.list_default(self.conn.network.security_groups())

    def list_servers(self):
        return self.list_default(self.conn.compute.servers())

    def list_keypairs(self):
        return self.list_default(self.conn.compute.keypairs())

    def get_keypair(self, keypair_id):
        try:
            keypair = self.conn.compute.get_keypair(keypair_id)
        except Exception as e:
            return "No Keypair found {0} | Error {1}".format(keypair_id, e)
        if keypair is None:
            raise "No Keypair  {0}".format(keypair_id)
        return keypair.to_dict()


    def import_keypair(self, keyname, public_key):
        """
        Import Keypair to OpenStack.

        :param keyname: Name of the Key
        :param public_key: The Key
        :return: Created Keypair
        """
        print(public_key)
        try:
            keypair = self.conn.compute.find_keypair(keyname)
            if not keypair:
                #self.logger.info("Create Keypair {0}".format(keyname))
                keypair = self.conn.compute.create_keypair(
                    name=keyname, public_key=public_key
                )
                return {"result":keypair, "message": "ok"}, 201
            elif keypair.public_key != public_key:
                #self.logger.info("Key has changed. Replace old Key")
                self.conn.compute.delete_keypair(keypair)
                keypair = self.conn.compute.create_keypair(
                    name=keyname, public_key=public_key
                )
                return keypair
            return keypair
        except Exception as e:
            return {"message": "Import Keypair {0} error:{1}".format(keyname, e), "result": {}}, 400


    def create_security_group(self, name):
        # self.logger.info("Create new security group {}".format(name))
        new_security_group = self.conn.network.create_security_group(name=name)
        return new_security_group

    def get_image(self, image):
        image = self.conn.compute.find_image(image)
        if image is None:
            #self.logger.exception("Image {0} not found!".format(image))
            raise Exception("Image {0} not found".format(image))

        return image

    def get_flavor(self, flavor):
        flavor = self.conn.compute.find_flavor(flavor)
        if flavor is None:
            # self.logger.exception("Flavor {0} not found!".format(flavor))
            raise Exception("Flavor {0} not found!".format(flavor)
            )
        return flavor

    def get_network(self):
        network = self.conn.network.find_network(self.NETWORK)
        if network is None:
            # self.logger.exception("Network {0} not found!".format(network))
            raise Exception("Network {0} not found!".format(network)
            )
        return network


    def get_security_group(self, security_group_id):
        security_group = self.conn.network.find_security_group(security_group_id)
        if security_group is None:
            raise Exception("Security group {0} not found!".format(security_group))
        return security_group

    def create_volume_by_start(self, volume_storage, volume_name, server_name):
        # self.logger.info("Creating volume with {0} GB diskspace".format(volume_storage))
        try:
            volume = self.conn.block_storage.create_volume(
                name=volume_name, size=int(volume_storage)).to_dict()
        except Exception as e:
            # self.logger.exception(
            #    "Trying to create volume with {0}"
            #    " GB for vm {1} error : {2}".format(volume_storage, server_name, e),exc_info=True)
            raise Exception(str(e))
        return volume["id"]

    def create_mount_init_script(self, volume_id):
        fileDir = os.path.dirname(os.path.abspath(__file__))
        mount_script = os.path.join(fileDir, "scripts/bash/mount.sh")
        with open(mount_script, "r") as file:
            text = file.read()
            text = text.replace("VOLUMEID", "virtio-" + volume_id[0:20])
            text = encodeutils.safe_encode(text.encode("utf-8"))
        init_script = base64.b64encode(text).decode("utf-8")
        return init_script

    def create_network(self):
        pass

    def set_network(self):
        networks = self.list_networks()
        networks = list(filter(lambda x: x["project_id"] == self.PROJECT_ID, networks))
        if not networks:
            self.create_network()
        self.NETWORK = networks[0]["id"]

    def start_server(
            self,
            flavor,
            image,
            key_name,
            public_key,
            servername,
            diskspace,
            volume_name,
    ):
        """
        Start a new Server.

        :param flavor: Name of flavor which should be used.
        :param image: Name of image which should be used
        :param public_key: Publickey which should be used
        :param servername: Name of the new server
        :param diskspace: Diskspace in GB for volume which should be created
        :param volume_name: Name of the volume
        :return: {'openstackid': serverId, 'volumeId': volumeId}
        """
        volume_id = ''
        #self.logger.info("Start Server {0}".format(servername))

    def add_security_group_rule(self, type, security_group_id):
        if type == "ssh":
            self.conn.network.create_security_group_rule(
                direction="ingress",
                protocol="tcp",
                port_range_max=22,
                port_range_min=22,
                security_group_id=security_group_id,
                ether_type="IPv4",

            )
        if type == "all_icmp":
            self.conn.network.create_security_group_rule(
                direction="ingress",
                protocol="ICMP",
                security_group_id=security_group_id,
                ether_type="IPv4",
                remote_ip_prefix= "0.0.0.0/0")


    def add_gateway_to_router(self, router_id, network_id):
        router = self.conn.network.get_router(router_id)
        if not router:
            raise Exception("Wrong router ID, router not found!")
        router_gateway_request = {"router":
            {
                "external_gateway_info": {
                    "network_id": network_id
                }
            }
        }
        return put("https://network.cloud.muni.cz/v2.0/routers/%s" % router_id,
            headers={"X-Auth-Token": self.conn.authorize()}, json=router_gateway_request).json()

        # TODO didnt work last time, check the issue page!
        # return router.add_gateway(self.SESSION, **router_gateway_request)
        # return self.conn.network.add_gateway_to_router(**router_gateway_request)

    def add_floating_ip_to_server(self, openstack_id, network):
        """
        Add a floating ip to a server.

        :param openstack_id: Id of the server
        :param network: Networkname which provides the floating ip
        :return: The floating ip
        """
        try:

            server = self.conn.compute.get_server(openstack_id)
            if server is None:
                #self.logger.exception("Instance {0} not found".format(openstack_id))
                raise Exception("Server not found")
            # self.logger.info("Checking if Server already got an Floating Ip")
            for values in server.addresses.values():
                for address in values:
                    if address["OS-EXT-IPS:type"] == "floating":
                        return address["addr"]
            # self.logger.info("Checking if unused Floating-Ip exist")

            for floating_ip in self.conn.network.ips():
                if not floating_ip.fixed_ip_address:
                    self.conn.compute.add_floating_ip_to_server(
                        server, floating_ip.floating_ip_address
                    )
                    # self.logger.info(
                    #     "Adding existing Floating IP {0} to {1}".format(
                    #         str(floating_ip.floating_ip_address), openstack_id
                    #     )
                    # )

                    return str(floating_ip.floating_ip_address)

            networkID = self.conn.network.find_network(network)
            if networkID is None:
                # self.logger.exception("Network " + network + " not found")
                raise Exception("Network not found")
            networkID = networkID.to_dict()["id"]
            floating_ip = self.conn.network.create_ip(floating_network_id=networkID)
            floating_ip = self.conn.network.get_ip(floating_ip)
            self.conn.compute.add_floating_ip_to_server(
                server, floating_ip.floating_ip_address
            )
            return floating_ip
        except Exception as e:
            # self.logger.exception(
            #     "Adding Floating IP to {0} with network {1} error:{2}".format(
            #         openstack_id, network, e
            #     )
            # )
            print(e)
            return

    def get_Image_with_Tag(self, id):
        """
        Get Image with Tags.

        :param id: Id of the image
        :return: Image instance
        """
        # self.logger.info("Get Image {0} with tags".format(id))
        try:
            images = self.conn.list_images()
            img = list(filter(lambda image: image["id"] == id, images))[0]
            metadata = img["metadata"]
            description = metadata.get("description")
            tags = img.get("tags")
            _image = image.Image(
                name=img["name"],
                min_disk=img["min_disk"],
                min_ram=img["min_ram"],
                status=img["status"],
                created_at=img["created_at"],
                updated_at=img["updated_at"],
                openstack_id=img["id"],
                description=description,
                tag=tags,
            )
            return _image
        except Exception as e:
            # self.logger.exception("Get Image {0} with Tag Error: {1}".format(id, e))
            return

    def get_server(self, openstack_id):
        """
        Get a server.

        :param openstack_id: Id of the server
        :return: Server instance
        """
        floating_ip = None
        fixed_ip = None
        #self.logger.info("Get Server {0}".format(openstack_id))
        try:
            _server = self.conn.compute.get_server(openstack_id)
        except Exception as e:
            # self.logger.exception("No Server found {0} | Error {1}".format(openstack_id, e))
            return "No Server found {0} | Error {1}".format(openstack_id, e)
        if _server is None:
            # self.logger.exception("No Server  {0}".format(openstack_id))
            raise "No Server  {0}".format(openstack_id)
        serv = _server.to_dict()
        return serv
        #TODO is this really needed?
        if serv["attached_volumes"]:
            volume_id = serv["attached_volumes"][0]["id"]
            diskspace = self.conn.block_storage.get_volume(volume_id).to_dict()["size"]
        else:
            diskspace = 0
        if serv["launched_at"]:
            dt = datetime.datetime.strptime(
                serv["launched_at"][:-7], "%Y-%m-%dT%H:%M:%S"
            )
            timestamp = time.mktime(dt.timetuple())
        else:
            timestamp = None
        try:
            flav = self.conn.compute.get_flavor(serv["flavor"]["id"]).to_dict()
        except Exception as e:
            # self.logger.exception(e)
            flav = None
        try:
            img = self.get_Image_with_Tag(serv["image"]["id"])
        except Exception as e:
            # self.logger.exception(e)
            img = None
        for values in _server.addresses.values():
            for address in values:

                if address["OS-EXT-IPS:type"] == "floating":
                    floating_ip = address["addr"]
                elif address["OS-EXT-IPS:type"] == "fixed":
                    fixed_ip = address["addr"]

        if floating_ip:
            to_return = server.Server(
                flav=flavor.Flavor(
                    vcpus=flav["vcpus"],
                    ram=flav["ram"],
                    disk=flav["disk"],
                    name=flav["name"],
                    openstack_id=flav["id"],
                ),
                img=img,
                status=serv["status"],
                metadata=serv["metadata"],
                project_id=serv["project_id"],
                keyname=serv["key_name"],
                openstack_id=serv["id"],
                name=serv["name"],
                created_at=str(timestamp),
                floating_ip=floating_ip,
                fixed_ip=fixed_ip,
                diskspace=diskspace,
            )
        else:
            to_return = server.Server(
                flav=flavor.Flavor(
                    vcpus=flav["vcpus"],
                    ram=flav["ram"],
                    disk=flav["disk"],
                    name=flav["name"],
                    openstack_id=flav["id"],
                ),
                img=img,
                status=serv["status"],
                metadata=serv["metadata"],
                project_id=serv["project_id"],
                keyname=serv["key_name"],
                openstack_id=serv["id"],
                name=serv["name"],
                created_at=str(timestamp),
                fixed_ip=fixed_ip,
                diskspace=diskspace,
            )
        return to_return

    def delete_keypair(self, key_name):
        key_pair = self.conn.compute.find_keypair(key_name)
        if key_pair:
            self.conn.compute.delete_keypair(key_pair)

'''


'''
   def get_client_version(self):
        """
        Get client version.

        :return: Version of the client.
        """
        # self.logger.info("Get Version of Client: {}".format(VERSION))
        return str(VERSION)

    

    


    def get_network(self):
        network = self.conn.network.find_network(self.NETWORK)
        if network is None:
            self.logger.exception("Network {0} not found!".format(network))
            raise networkNotFoundException(
                Reason="Network {0} not found!".format(network)
            )
        return network


    def create_volume(self, volume_name, diskspace):
        """
        Create volume.
        :param volume_name: Name of volume
        :param diskspace: Diskspace in GB for new volume
        :return: Id of new volume
        """
        self.logger.info("Creating volume with {0} GB diskspace".format(diskspace))
        try:
            volume = self.conn.block_storage.create_volume(
                name=volume_name, size=int(diskspace)
            ).to_dict()
            volumeId = volume["id"]
            return volumeId
        except Exception as e:
            self.logger.exception(
                "Trying to create volume with {0} GB  error : {1}".format(diskspace, e),
                exc_info=True,
            )

            raise ressourceException(Reason=str(e))


    def start_server_with_custom_key(self, flavor, image, servername, elixir_id, diskspace,
                                     volumename):

        """
        Start a new Server.

        :param flavor: Name of flavor which should be used.
        :param image: Name of image which should be used
        :param public_key: Publickey which should be used
        :param servername: Name of the new server
        :param elixir_id: Elixir_id of the user who started a new server
        :param diskspace: Diskspace in GB for volume which should be created
        :param volumename: Name of the volume
        :return: {'openstackid': serverId, 'volumeId': volumeId}
        """
        self.logger.info("Start Server {} with custom key".format(servername))
        volume_id = ''
        try:
            metadata = {"elixir_id": elixir_id}
            image = self.get_image(image=image)
            flavor = self.get_flavor(flavor=flavor)
            network = self.get_network()
            private_key = self.conn.create_keypair(name=servername).__dict__['private_key']
            if int(diskspace) > 0:
                volume_id = self.create_volume_by_start(volume_storage=diskspace,
                                                        volume_name=volumename,
                                                        server_name=servername)
                init_script = self.create_mount_init_script(volume_id=volume_id)

                server = self.conn.compute.create_server(
                    name=servername,
                    image_id=image.id,
                    flavor_id=flavor.id,
                    networks=[{"uuid": network.id}],
                    key_name=servername,
                    metadata=metadata,
                    user_data=init_script,
                    availability_zone=self.AVAIALABILITY_ZONE,
                )
            else:
                server = self.conn.compute.create_server(
                    name=servername,
                    image_id=image.id,
                    flavor_id=flavor.id,
                    networks=[{"uuid": network.id}],
                    key_name=servername,
                    metadata=metadata,
                )

            openstack_id = server.to_dict()["id"]
            global osi_key_dict
            osi_key_dict[openstack_id] = dict(key=private_key, name=servername,
                                              status=self.PREPARE_BIOCONDA_BUILD)
            return {"openstackid": openstack_id, "volumeId": volume_id, 'private_key': private_key}
        except Exception as e:
            self.delete_keypair(key_name=servername)
            self.logger.exception("Start Server {1} error:{0}".format(e, servername))
            return {}

    def create_and_deploy_playbook(self, private_key, play_source, openstack_id):
        # get ip and port for inventory
        fields = self.get_ip_ports(openstack_id=openstack_id)
        global osi_key_dict
        key_name = osi_key_dict[openstack_id]['name']
        playbook = BiocondaPlaybook(fields["IP"], fields["PORT"], play_source,
                                    osi_key_dict[openstack_id]["key"], private_key)
        osi_key_dict[openstack_id]["status"] = self.BUILD_BIOCONDA
        playbook.run_it()
        osi_key_dict[openstack_id]["status"] = self.ACTIVE
        self.delete_keypair(key_name=key_name)
        return 0

    def attach_volume_to_server(self, openstack_id, volume_id):
        """
        Attach volume to server.

        :param openstack_id: Id of server
        :param volume_id: Id of volume
        :return: True if attached, False if not
        """

        def checkStatusVolume(volume, conn):
            self.logger.info("Checking Status Volume {0}".format(volume_id))
            done = False
            while not done:

                status = conn.block_storage.get_volume(volume).to_dict()["status"]
                self.logger.info("Volume {} Status:{}".format(volume_id, status))
                if status == "in-use":
                    return False

                if status != "available":

                    time.sleep(3)
                else:
                    done = True
                    time.sleep(2)
            return True

        server = self.conn.compute.get_server(openstack_id)
        if server is None:
            self.logger.exception("No Server  {0} ".format(openstack_id))
            raise serverNotFoundException(Reason="No Server {0}".format(openstack_id))
        if checkStatusVolume(volume_id, self.conn):

            self.logger.info(
                "Attaching volume {0} to virtualmachine {1}".format(
                    volume_id, openstack_id
                )
            )
            try:
                self.conn.compute.create_volume_attachment(
                    server=server, volumeId=volume_id
                )
            except Exception as e:
                self.logger.exception(
                    "Trying to attache volume {0} to vm {1} error : {2}".format(
                        volume_id, openstack_id, e
                    ),
                    exc_info=True,
                )
                self.logger.info("Delete Volume  {0}".format(volume_id))
                self.conn.block_storage.delete_volume(volume=volume_id)
                return False

            return True
        return True

    def check_server_status(self, openstack_id, diskspace, volume_id):
        """
        Check status of server.

        :param openstack_id: Id of server
        :param diskspace: diskspace of server(volume will be attached if server
                is active and diskpace >0)
        :param volume_id: Id of volume
        :return: server instance
        """
        # TODO: Remove diskspace param, if volume_id exist it can be attached
        # diskspace not need
        self.logger.info("Check Status VM {0}".format(openstack_id))
        try:
            server = self.conn.compute.get_server(openstack_id)
        except Exception:
            self.logger.exception("No Server with id  {0} ".format(openstack_id))
            return None
        if server is None:
            self.logger.exception("No Server with id {0} ".format(openstack_id))
            return None
        serv = server.to_dict()

        try:
            global osi_key_dict
            if serv["status"] == self.ACTIVE:
                host = self.get_server(openstack_id).floating_ip
                port = self.SSH_PORT

                if self.USE_GATEWAY:
                    serv_cop = self.get_server(openstack_id)
                    server_base = serv_cop.fixed_ip.split(".")[-1]
                    host = str(self.GATEWAY_IP)
                    port = int(self.GATEWAY_BASE) + int(server_base) * 3
                elif self.get_server(openstack_id).floating_ip is None:
                    host = self.add_floating_ip_to_server(
                        openstack_id, self.FLOATING_IP_NETWORK
                    )
                if self.netcat(host, port):
                    server = self.get_server(openstack_id)

                    if diskspace > 0:
                        attached = self.attach_volume_to_server(
                            openstack_id=openstack_id, volume_id=volume_id
                        )

                        if attached is False:
                            self.delete_server(openstack_id=openstack_id)
                            server.status = "DESTROYED"
                            return server

                    if openstack_id in osi_key_dict:
                        if osi_key_dict[openstack_id][
                            "status"] == self.PREPARE_BIOCONDA_BUILD:
                            server.status = self.PREPARE_BIOCONDA_BUILD
                            return server
                        elif osi_key_dict[openstack_id][
                            "status"] == self.BUILD_BIOCONDA:
                            server.status = self.BUILD_BIOCONDA
                            return server
                        else:
                            return server
                    return self.get_server(openstack_id)
                else:
                    server = self.get_server(openstack_id)
                    server.status = "PORT_CLOSED"
                    return server
            else:
                server = self.get_server(openstack_id)
                server.status = self.BUILD
                return server
        except Exception as e:
            self.logger.exception("Check Status VM {0} error: {1}".format(openstack_id, e))
            return None

    def add_security_group_to_server(self, http, https, udp, server_id):
        """
        Adds the default simple vm security group to the vm.
        Also adds a security group which can open http,https and udp ports.
        :param http: If http ports should be open
        :param https: If https ports should be open
        :param udp: If udp ports should be open
        :param server_id: The id of the server
        :return:
        """

        standart_default_security_group = self.conn.network.find_security_group(
            name_or_id=self.OPENSTACK_DEFAULT_SECURITY_GROUP)
        default_security_group_simple_vm = self.conn.network.get_security_group(
            security_group=self.DEFAULT_SECURITY_GROUP)

        if standart_default_security_group:
            self.logger.info("Remove default OpenStack security  from  {}".format(server_id))

            self.conn.compute.remove_security_group_from_server(server=server_id,
                                                                security_group=standart_default_security_group)
        if default_security_group_simple_vm:
            self.logger.info(
                "Add default simple vm security group {} to {}".format(self.DEFAULT_SECURITY_GROUP,
                                                                       server_id))
            self.conn.compute.add_security_group_to_server(
                server=server_id, security_group=default_security_group_simple_vm
            )

        ip_base = \
            list(self.conn.compute.server_ips(server=server_id))[0].to_dict()['address'].split(".")[
                -1]

        udp_port_start = int(ip_base) * 10 + int(self.UDP_BASE)

        security_group = self.conn.network.find_security_group(name_or_id=server_id)
        if security_group:
            self.conn.compute.remove_security_group_from_server(server=server_id,
                                                                security_group=security_group)
            self.conn.network.delete_security_group(security_group)

        security_group = self.create_security_group(
            name=server_id,
            udp_port_start=udp_port_start,
            udp=udp,
            ssh=True,
            https=https,
            http=http,
        )
        self.conn.compute.add_security_group_to_server(
            server=server_id, security_group=security_group
        )

        return True

    def get_ip_ports(self, openstack_id):
        """
        Get Ip and Port of the sever.

        :param openstack_id: Id of the server
        :return: {'IP': ip, 'PORT': port, 'UDP':start_port}
        """
        self.logger.info("Get IP and PORT for server {0}".format(openstack_id))

        # check if gateway is active
        try:
            if self.USE_GATEWAY:
                server = self.get_server(openstack_id)
                server_base = server.fixed_ip.split(".")[-1]
                port = int(self.GATEWAY_BASE) + int(server_base) * 3
                udp_port_start = int(server_base) * 10 + int(self.UDP_BASE)
                return {"IP": str(self.GATEWAY_IP), "PORT": str(port), "UDP": str(udp_port_start)}

            else:
                # todo security groups floating ips
                floating_ip = self.get_server(openstack_id)
                return {"IP": str(floating_ip)}
        except Exception as e:
            self.logger.exception(
                "Get IP and PORT for server {0} error:".format(openstack_id, e)
            )
            return {}

    def create_snapshot(self, openstack_id, name, elixir_id, base_tag, description):
        """
        Create an Snapshot from an server.

        :param openstack_id: Id of the server
        :param name: Name of the Snapshot
        :param elixir_id: Elixir Id of the user who requested the creation
        :param base_tag: Tag with which the servers image is also tagged
        :return: Id of the new Snapshot
        """
        self.logger.info(
            "Create Snapshot from Instance {0} with name {1} for {2}".format(
                openstack_id, name, elixir_id
            )
        )

        try:
            snapshot_munch = self.conn.create_image_snapshot(
                server=openstack_id, name=name
            )
        except Exception:
            self.logger.exception("Instance {0} not found".format(openstack_id))
            return
        try:
            snapshot = self.conn.get_image_by_id(snapshot_munch["id"])
            snapshot_id = snapshot["id"]
            # todo check again
            try:
                image = self.conn.get_image(name_or_id=snapshot_id)
                if description:
                    self.conn.update_image_properties(
                        image=image,
                        meta={'description': description})

                self.conn.image.add_tag(
                    image=snapshot_id, tag="snapshot_image:{0}".format(base_tag)
                )
            except Exception:
                self.logger.exception("Tag error catched")
                pass
            try:
                self.conn.image.add_tag(image=snapshot_id, tag=elixir_id)
            except Exception:
                pass

            return snapshot_id
        except Exception as e:
            self.logger.exception(
                "Create Snapshot from Instance {0}"
                " with name {1} for {2} error : {3}".format(
                    openstack_id, name, elixir_id, e
                )
            )
            return

    def delete_image(self, image_id):
        """
        Delete Image.

        :param image_id: Id of the image
        :return: True if deleted, False if not
        """
        self.logger.info("Delete Image {0}".format(image_id))
        try:
            image = self.conn.compute.get_image(image_id)
            if image is None:
                self.logger.exception("Image {0} not found!".format(image))
                raise imageNotFoundException(
                    Reason=("Image {0} not found".format(image))
                )
            self.conn.compute.delete_image(image)
            return True
        except Exception as e:
            self.logger.exception("Delete Image {0} error : {1}".format(image_id, e))
            return False

    def add_floating_ip_to_server(self, openstack_id, network):
        """
        Add a floating ip to a server.

        :param openstack_id: Id of the server
        :param network: Networkname which provides the floating ip
        :return: The floating ip
        """
        try:

            server = self.conn.compute.get_server(openstack_id)
            if server is None:
                self.logger.exception("Instance {0} not found".format(openstack_id))
                raise serverNotFoundException
            self.logger.info("Checking if Server already got an Floating Ip")
            for values in server.addresses.values():
                for address in values:
                    if address["OS-EXT-IPS:type"] == "floating":
                        return address["addr"]
            self.logger.info("Checking if unused Floating-Ip exist")

            for floating_ip in self.conn.network.ips():
                if not floating_ip.fixed_ip_address:
                    self.conn.compute.add_floating_ip_to_server(
                        server, floating_ip.floating_ip_address
                    )
                    self.logger.info(
                        "Adding existing Floating IP {0} to {1}".format(
                            str(floating_ip.floating_ip_address), openstack_id
                        )
                    )
                    return str(floating_ip.floating_ip_address)

            networkID = self.conn.network.find_network(network)
            if networkID is None:
                self.logger.exception("Network " + network + " not found")
                raise networkNotFoundException
            networkID = networkID.to_dict()["id"]
            floating_ip = self.conn.network.create_ip(floating_network_id=networkID)
            floating_ip = self.conn.network.get_ip(floating_ip)
            self.conn.compute.add_floating_ip_to_server(
                server, floating_ip.floating_ip_address
            )

            return floating_ip
        except Exception as e:
            self.logger.exception(
                "Adding Floating IP to {0} with network {1} error:{2}".format(
                    openstack_id, network, e
                )
            )
            return

    def netcat(self, host, port):
        """
        Try to connect to specific host:port.

        :param host: Host to connect
        :param port: Port to connect
        :return: True if successfully connected, False if not
        """
        self.logger.info("Checking SSH Connection {0}:{1}".format(host, port))
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            r = sock.connect_ex((host, port))
            self.logger.info(
                "Checking SSH Connection {0}:{1} Result = {2}".format(host, port, r)
            )
            if r == 0:
                return True
            else:
                return False

    def delete_server(self, openstack_id):
        """
        Delete Server.

        :param openstack_id: Id of the server
        :return: True if deleted, False if not
        """
        self.logger.info("Delete Server {0}".format(openstack_id))
        try:
            server = self.conn.compute.get_server(openstack_id)
            if server is None:
                self.logger.exception("Instance {0} not found".format(openstack_id))
                raise serverNotFoundException

            if server.status == "SUSPENDED":
                self.conn.compute.resume_server(server)
                server = self.conn.compute.get_server(server)
                self.conn.compute.wait_for_server(server=server, status='ACTIVE')
            self.logger.info(server)
            self.logger.info(server.name)
            security_group = self.conn.network.find_security_group(name_or_id=openstack_id)
            if security_group:
                self.logger.info("Delete security group {}".format(openstack_id))
                self.conn.compute.remove_security_group_from_server(server=server,
                                                                    security_group=security_group)
                self.conn.network.delete_security_group(security_group)
            self.conn.compute.delete_server(server)

            return True
        except Exception as e:
            self.logger.exception("Delete Server {0} error: {1}".format(openstack_id, e))
            return False

    def delete_volume_attachment(self, volume_id, server_id):
        """
        Delete volume attachment.

        :param volume_id: Id of the attached volume
        :param server_id: Id of the server where the volume is attached
        :return: True if deleted, False if not
        """
        try:
            attachments = self.conn.block_storage.get_volume(volume_id).attachments
            for attachment in attachments:
                volume_attachment_id = attachment["id"]
                instance_id = attachment["server_id"]
                if instance_id == server_id:
                    self.logger.info(
                        "Delete Volume Attachment  {0}".format(volume_attachment_id)
                    )
                    self.conn.compute.delete_volume_attachment(
                        volume_attachment=volume_attachment_id, server=server_id
                    )
            return True
        except Exception as e:
            self.logger.exception(
                "Delete Volume Attachment  {0} error: {1}".format(
                    volume_attachment_id, e
                )
            )
            return False

    def delete_volume(self, volume_id):
        """
        Delete volume.

        :param volume_id: Id of the volume
        :return: True if deleted, False if not
        """

        def checkStatusVolume(volume, conn):
            self.logger.info("Checking Status Volume {0}".format(volume_id))
            done = False
            while not done:

                status = conn.block_storage.get_volume(volume).to_dict()["status"]

                if status != "available":

                    time.sleep(3)
                else:
                    done = True
            return volume

        try:
            checkStatusVolume(volume_id, self.conn)
            self.logger.info("Delete Volume  {0}".format(volume_id))
            self.conn.block_storage.delete_volume(volume=volume_id)
            return True
        except Exception as e:
            self.logger.exception("Delete Volume {0} error".format(volume_id, e))
            return False

    def stop_server(self, openstack_id):
        """
        Stop server.

        :param openstack_id: Id of the server.
        :return: True if resumed, False if not
        """
        self.logger.info("Stop Server {0}".format(openstack_id))
        server = self.conn.compute.get_server(openstack_id)
        try:
            if server is None:
                self.logger.exception("Instance {0} not found".format(openstack_id))
                raise serverNotFoundException

            if server.status == "ACTIVE":
                self.conn.compute.suspend_server(server)
                server = self.conn.compute.get_server(server)
                while server.status != "SUSPENDED":
                    server = self.conn.compute.get_server(server)
                    time.sleep(3)

                return True
            else:

                return False
        except Exception as e:
            self.logger.exception("Stop Server {0} error:".format(openstack_id, e))

            return False

    def reboot_server(self, server_id, reboot_type):
        """
        Reboot server.

        :param server_id: Id of the server
        :param reboot_type: HARD or SOFT
        :return:  True if resumed, False if not
        """
        self.logger.info("Reboot Server {} {}".format(server_id, reboot_type))
        try:
            server = self.conn.compute.get_server(server_id)
            if server is None:
                self.logger.exception("Instance {0} not found".format(server_id))
                raise serverNotFoundException
            else:
                self.conn.compute.reboot_server(server, reboot_type)
                return True
        except Exception as e:
            self.logger.exception(
                "Reboot Server {} {} Error : {}".format(server_id, reboot_type, e)
            )
            return False

    def resume_server(self, openstack_id):
        """
        Resume stopped server.

        :param openstack_id: Id of the server.
        :return: True if resumed, False if not
        """
        self.logger.info("Resume Server {0}".format(openstack_id))
        try:
            server = self.conn.compute.get_server(openstack_id)
            if server is None:
                self.logger.exception("Instance {0} not found".format(openstack_id))
                raise serverNotFoundException

            if server.status == "SUSPENDED":
                self.conn.compute.resume_server(server)
                while server.status != "ACTIVE":
                    server = self.conn.compute.get_server(server)
                    time.sleep(3)

                return True
            else:

                return False
        except Exception as e:
            self.logger.exception("Resume Server {0} error:".format(openstack_id, e))
            return False

    def create_security_group(
            self, name, udp_port_start=None, ssh=True, http=False, https=False, udp=False
    ):
        self.logger.info("Create new security group {}".format(name))
        new_security_group = self.conn.network.create_security_group(name=name)
        if http:
            self.logger.info("Add http rule to security group {}".format(name))
            self.conn.network.create_security_group_rule(
                direction="ingress",
                protocol="tcp",
                port_range_max=80,
                port_range_min=80,
                security_group_id=new_security_group["id"],
            )
            self.conn.network.create_security_group_rule(
                direction="ingress",
                ether_type="IPv6",
                protocol="tcp",
                port_range_max=80,
                port_range_min=80,
                security_group_id=new_security_group["id"],
            )

        if https:
            self.logger.info("Add https rule to security group {}".format(name))

            self.conn.network.create_security_group_rule(
                direction="ingress",
                protocol="tcp",
                port_range_max=443,
                port_range_min=443,
                security_group_id=new_security_group["id"],
            )
            self.conn.network.create_security_group_rule(
                direction="ingress",
                ether_type="IPv6",
                protocol="tcp",
                port_range_max=443,
                port_range_min=443,
                security_group_id=new_security_group["id"],
            )
        if udp:
            self.logger.info(
                "Add udp rule ports {} - {} to security group {}".format(
                    udp_port_start, udp_port_start + 9, name
                )
            )

            self.conn.network.create_security_group_rule(
                direction="ingress",
                protocol="udp",
                port_range_max=udp_port_start + 9,
                port_range_min=udp_port_start,
                security_group_id=new_security_group["id"],
            )
            self.conn.network.create_security_group_rule(
                direction="ingress",
                ether_type="IPv6",
                protocol="udp",
                port_range_max=udp_port_start + 9,
                port_range_min=udp_port_start,
                security_group_id=new_security_group["id"],
            )
        if ssh:
            self.logger.info("Add ssh rule to security group {}".format(name))

            self.conn.network.create_security_group_rule(
                direction="ingress",
                protocol="tcp",
                port_range_max=22,
                port_range_min=22,
                security_group_id=new_security_group["id"],
            )
            self.conn.network.create_security_group_rule(
                direction="ingress",
                ether_type="IPv6",
                protocol="tcp",
                port_range_max=22,
                port_range_min=22,
                security_group_id=new_security_group["id"],
            )

        return new_security_group

    def get_limits(self):
        """
        Get the Limits.

        (maxTotalVolumes,maxTotalVolumeGigabytes,
        maxTotalInstances,totalRamUsed,totalInstancesUsed)
        of the OpenStack Project from the Client.

        :return: {'maxTotalVolumes': maxTotalVolumes, '
                maxTotalVolumeGigabytes': maxTotalVolumeGigabytes,
                'maxTotalInstances': maxTotalInstances,
                 'totalRamUsed': totalRamUsed,
                'totalInstancesUsed': totalFlInstancesUsed}
        """
        self.logger.info("Get Limits")
        limits = self.conn.get_compute_limits()
        limits.update(self.conn.get_volume_limits())
        maxTotalVolumes = str(limits["absolute"]["maxTotalVolumes"])
        maxTotalInstances = str(limits["max_total_instances"])
        maxTotalVolumeGigabytes = str(limits["absolute"]["maxTotalVolumeGigabytes"])
        totalRamUsed = str(limits["total_ram_used"])
        totalInstancesUsed = str(limits["total_instances_used"])
        return {
            "maxTotalVolumes": maxTotalVolumes,
            "maxTotalVolumeGigabytes": maxTotalVolumeGigabytes,
            "maxTotalInstances": maxTotalInstances,
            "totalRamUsed": totalRamUsed,
            "totalInstancesUsed": totalInstancesUsed,
        }

'''
