#!/usr/bin/python
# -*- coding: utf-8 -*-


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = ''' '''

import acos_client as acos
from acos_client import errors as acos_errors

def main():
    argument_spec = a10_argument_spec()
    argument_spec.update(url_argument_spec())
    argument_spec.update(
        dict(
            state=dict(type='str', default='present', choices=['present', 'absent'])
            service_group=dict(type='str', aliases=['service', 'pool', 'group'], required=True),
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
                                               'src-ip-hash'])
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
    sg_name = module.params['service_group']
    protocol = module.params['service_group_protocol']
    method = module.params['service_group_method']
    servers = module.params['servers']

    if sg_name is None:
        module.fail_json(msg='service_group is required')

    acos_client = acos.Client(host, acos.AXAPI_30, username, password)

    changed = False
    if state == 'absent':
        member_list = acos_client.slb.service_group.member.get_list(sg_name);

        for member in member_list['member-list']:
            result = acos_client.slb.service_group.member.delete(sg_name,
                                                                 member['name'],
                                                                 member['port'])
        result = acos_client.slb.service_group.delete(sg_name)
        changed = True

    else if state == 'present':
        try:
            result = acos_client.slb.service_group.create(sg_name, protocol, lb_method)
        except acos_errors.Exists:
            result = acos_client.slb.service_group.update(sg_name, protocol,
                                                          lb_method, health_monitor)

        for server in servers:
            
