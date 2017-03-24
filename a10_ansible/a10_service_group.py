#!/usr/bin/python
# -*- coding: utf-8 -*-


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = ''' '''

VALID_SERVICE_GROUP_FIELDS = ['name', 'protocol', 'lb_method']
VALID_SERVER_FIELDS = ['server', 'port', 'status']


def get_member_server(acos_client, sg_name, server_name, port):
    try:
        return acos_client.slb.service_group.member.get(sg_name,
                server_name,
                port)
    except acos_errors.NotFound:
        pass

def check_update_member(acos_client, server, slb_server):
    for k,v in server.items():
        if not slb_server[""][k] == v:
            return True
    return False

def get_service_group(acos_client, sg_name):
    try:
        return acos_client.slb.service_group.get(sg_name)
    except acos_errors.NotFound:
        pass

def check_update_sg(acos_client, service_group, slb_sg):
    for k,v in service_group.items():
        if not slb_sg["service_group"][k] == v:
            return True
    return False

def main():
    argument_spec = a10_argument_spec()
    argument_spec.update(url_argument_spec())
    argument_spec.update(
        dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            service_group=dict(type='str', required=True, aliases=['service', 'pool', 'group', 'name']),
            service_group_protocol=dict(type='str', default='tcp', aliases=['proto', 'protocol'],
                                        choices=['tcp', 'udp']),
            service_group_method=dict(type='str', defaut='round-robin',
                                      aliases=['method'],
                                      choices=['round-robin',
                                               'weighted-rr',
                                               'least-connection',
                                               'weighted-least-connection',
                                               'service-least-connection',
                                               'service-weighted-least-connection',
                                               'fastest-response',
                                               'round-robin-strict',
                                               'src-ip-only-hash',
                                               'src-ip-hash']),
            servers=dict(type='list', aliases=['server','member'], default=[]),
            partition=dict(type='str', default=[]),
        )
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False,
    )

    host = module.params['host']
    username = module.params['username']
    password = module.params['password']
    partition = module.params['partition']
    state = module.params['state']
    write_config = module.params['write_config']
    service_group = module.params['service_group']
    servers = module.params['servers']

    sg_name = service_group["name"]
    lb_method = service_group["method"]
    protocol = service_group["protocol"]

    if sg_name is None:
        module.fail_json(msg='service_group is required')

    acos_client = acos.Client(host, "3.0", username, password)

    changed = False
    try:
        if state == 'absent':
            member_list = acos_client.slb.service_group.member.get_list(sg_name);

            for member in member_list['member-list']:
                result = acos_client.slb.service_group.member.delete(sg_name,
                                                                     member['name'],
                                                                     member['port'])
            try:
                result = acos_client.slb.service_group.delete(sg_name)
                changed = True
            except acos_errors.NotFound:
                module.fail_json(msg="service group does not exist")

        elif state == 'present':
            slb_sg = get_service_group(sg_name)

            if slb_sg:
                update = check_update_sg(acos_client, service_group, slb_sg)

                if update:
                    result = acos_client.slb.service_group.update(sg_name, protocol,
                                                                  lb_method, health_monitor=None)
                    changed = True
                    LOG.debug("Updated service group") 
            else:
                result = acos_client.slb.service_group.create(sg_name, protocol, lb_method)
                changed = True
                LOG.debug("Created service group")

            for server in servers:
                slb_server = get_member_server(sg_name, server["name"], server["port"])

                if slb_server:
                    update = check_update_server(acos_client, server, slb_server)

                    if update:
                        result = acos_client.slb.member.update(sg_name, server["name"],
                                                               server["port"])
                        changed = True
                        LOG.debug("Updated member server")
                else:
                    acos_client.slb.server.create(server["name"], server["ip_address"])
                    result = acos_client.slb.member.associate()

    except Exception as e:
        module.fail_json(msg=("Caught exception: {0}").format(e))

    module.exit_json(changed=changed, content=result)


import logging as LOG
LOG.basicConfig(filename=".debug", level=LOG.DEBUG)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import url_argument_spec 

import a10_base
import acos_client as acos
from acos_client import errors as acos_errors

if __name__ == '__main__':
    main()
