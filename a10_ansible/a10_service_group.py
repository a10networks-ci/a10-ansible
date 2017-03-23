#!/usr/bin/python
# -*- coding: utf-8 -*-


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = ''' '''

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
    sg_name = module.params['name']
    protocol = module.params['service_group_protocol']
    method = module.params['service_group_method']
    servers = module.params['servers']

    LOG.debug("MODULE PARAMS NOT BROKEN")

    if sg_name is None:
        module.fail_json(msg='service_group is required')

    acos_client = acos.Client(host, "3.0", username, password)

    LOG.debug("ACOS CLIENT NOT BROKEN")

    changed = False
    result = None
    try:
        if state == 'absent':
            member_list = acos_client.slb.service_group.member.get_list(sg_name);

            for member in member_list['member-list']:
                result = acos_client.slb.service_group.member.delete(sg_name,
                                                                     member['name'],
                                                                     member['port'])
            result = acos_client.slb.service_group.delete(sg_name)
        
            if result["response"]["status"] == "fail":
                module.fail_json(msg="service group does not exist")
            else:
                changed = True

        elif state == 'present':
            try:
                result = acos_client.slb.service_group.create(sg_name, protocol, method)
                changed = True
            except acos_errors.Exists:
                result = acos_client.slb.service_group.update(sg_name, protocol,
                                                              method, health_monitor=None)

    except Exception as e:
        module.fail_json(msg=("Caught exception: {0}").format(e))

    module.exit_json(changed=changed, content=result)


import json
import logging as LOG
LOG.basicConfig(filename="test1.log", level=LOG.DEBUG)
LOG.debug("SANITY")

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import url_argument_spec
from ansible.module_utils.a10 import a10_argument_spec

import acos_client as acos
from acos_client import errors as acos_errors

if __name__ == '__main__':
    main()
