#!/usr/bin/python
# -*- coding: utf-8 -*-


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = ''' '''

VALID_SERVICE_GROUP_FIELDS = ['name', 'service_group', 'protocol', 'lb_method']
VALID_SERVER_FIELDS = ['server', 'port', 'status']

def standardize_members(members):
    for member in members:
        if member.get("state") == "disabled":
            member["state"] = 1
        else:
            member["state"] = 0
    return members

def get_member_server(acos_client, sg_name, member_name, port):
    try:
        return acos_client.slb.service_group.member.get(sg_name,
                member_name,
                port)
    except acos_errors.NotFound:
        pass

def check_update_member(acos_client, member, slb_member):
    member["member-state"] = member.pop("state")
    if member["member-state"] == 1:
        member["member-state"] = "disable"
    else:
        member["member-state"] = "enable"
    for k,v in member.items():
        if not slb_member["member"].get(k) == v:
            LOG.debug("*******POS*******")
            LOG.debug(v)
            return True
    return False

def get_service_group(acos_client, sg_name):
    return acos_client.slb.service_group.get(sg_name)
    try:
        LOG.debug("*********NAME******")
        LOG.debug(sg_name)
        LOG.debug(acos_client.slb.service_group.get(sg_name))
    except acos_errors.NotFound:
        return None

def check_update_sg(acos_client, service_group, slb_sg):
   for k,v in service_group.items():
        if not slb_sg["service-group"][k] == v:
            return True
   return False

def main():
    argument_spec = a10_argument_spec()
    argument_spec.update(url_argument_spec())
    argument_spec.update(
        dict(
            state=dict(type='str', default='present', choices=['present', 'absent']),
            service_group=dict(type='str', required=True, aliases=['service_group', 'pool', 'group', 'name']),
            service_group_protocol=dict(type='str', default='tcp', aliases=['proto', 'protocol'],
                                        choices=['tcp', 'udp']),
            service_group_method=dict(type='str', defaut='round-robin',
                                      aliases=['lb_method'],
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
            members=dict(type='list', aliases=['member'], default=[]),
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
    members = module.params['members']

    sg_name = module.params["name"]
    lb_method = module.params["lb_method"]
    protocol = module.params["protocol"]

    members = standardize_members(members)

    if sg_name is None:
        module.fail_json(msg='service_group is required')

    acos_client = acos.Client(host, "3.0", username, password)

    changed = False
    result = None
    
    try:
        if state == 'absent':
            member_list = acos_client.slb.service_group.member.get_list(sg_name);

            for member in member_list['member-list']:
                result = acos_client.slb.service_group.member.delete(sg_name,
                                                                     member['name'],
                                                                     member['port'])
                changed = True
            try:
                result = acos_client.slb.service_group.delete(sg_name)
                changed = True
            except acos_errors.NotFound:
                module.fail_json(msg="service group does not exist")
        
        elif state == 'present':
            slb_sg = get_service_group(acos_client, sg_name)
            result = slb_sg
            if slb_sg:
                service_group = dict(name=sg_name, protocol=protocol)
                service_group["lb-method"] = lb_method


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

            for member in members:
                slb_member = get_member_server(acos_client, sg_name, member["name"], member["port"])
                if slb_member:
                    update = check_update_member(acos_client, member, slb_member)
                    if update:
                        result = acos_client.slb.service_group.member.update(sg_name,
                                                                             member["name"],
                                                                             member["port"])
                                                                             #member_state=member["member-state"])
                        changed = True
                        LOG.debug("Updated member server")
                else:
                    result = acos_client.slb.service_group.member.associate(sg_name,
                                                                            member["name"],
                                                                            member["port"])
                                                                            #member_state=member["state"])
                    changed = True
                    LOG.debug("Associated member server")

    except Exception as e:
        module.fail_json(msg=("Caught exception: {0}").format(e))
    LOG.debug(result)
    module.exit_json(changed=changed, content=result)


import logging as LOG
LOG.basicConfig(filename=".debug", level=LOG.DEBUG)

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import url_argument_spec 
from ansible.module_utils.a10 import axapi_call, a10_argument_spec, axapi_authenticate, axapi_failure, axapi_enabled_disabled

import acos_client as acos
from acos_client import errors as acos_errors

if __name__ == '__main__':
    main()
