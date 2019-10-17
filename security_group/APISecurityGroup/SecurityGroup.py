class SecurityGroup:

    def create(self, connection, name):
        try:
            new_security_group = connection.network.create_security_group(name=name)
            return new_security_group, 201
        except Exception as e:
            return {"message": str(e)}, 409

    def get(self,connection, security_group_id):
        security_group = connection.network.find_security_group(security_group_id)
        if security_group is None:
            return {}, 404
        return security_group.to_dict(), 200

    def list(self, connection):
        tmp = connection.network.security_groups()
        return [r for r in tmp], 200

    def update(self):
        return {}, 501

    def delete(self):
        return {}, 501

class SecurityGroupRule:

    def create(self,connection, security_group_id, type):

        try:
            if type == "ssh":
                new_rule = connection.network.create_security_group_rule(
                    direction="ingress",
                    protocol="tcp",
                    port_range_max=22,
                    port_range_min=22,
                    security_group_id=security_group_id,
                    ether_type="IPv4")
            if type == "all_icmp":
                new_rule = connection.network.create_security_group_rule(
                    direction="ingress",
                    protocol="ICMP",
                    security_group_id=security_group_id,
                    ether_type="IPv4",
                    remote_ip_prefix="0.0.0.0/0")
            if type == "http":
                new_rule = connection.network.create_security_group_rule(
                    direction="ingress",
                    protocol="HTTP",
                    security_group_id=security_group_id,
                    ethertype="IPv4",
                    remote_ip_prefix="0.0.0.0/0")

            if type == "https":
                new_rule = connection.network.create_security_group_rule(
                    direction="ingress",
                    protocol="HTTPS",
                    security_group_id=security_group_id,
                    ethertype="IPv4",
                    remote_ip_prefix="0.0.0.0/0")

            return new_rule.to_dict(), 201
        except Exception as e:
            return {"message": str(e)}, 409

    def get(self, security_group_id, security_group_rule_id):
        return {}, 501

    def list(self, security_group_id):
        return {}, 501

    def update(self, security_group_id):
        return {}, 501

    def delete(self, security_group_id):
        return {}, 501