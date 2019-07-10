#!/usr/bin/env python
#
# Exercise the opsramp module as an illustration of how to use it.
#
# (c) Copyright 2019 Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
import os

import opsramp.binding
import opsramp.rba
import opsramp.msp


CATEGORY_NAME = 'Testing 123'


def main():
    OPSRAMP_URL = os.environ['OPSRAMP_URL']
    TENANT_ID = os.environ['OPSRAMP_TENANT_ID']
    KEY = os.environ['OPSRAMP_KEY']
    SECRET = os.environ['OPSRAMP_SECRET']

    ormp = opsramp.binding.connect(OPSRAMP_URL, KEY, SECRET)

    # Print some random global "stuff" just to show that we can.
    cfg = ormp.config()
    print('alert types', cfg.get_alert_types())
    print('channels', cfg.get_channels())
    print('countries', len(cfg.get_countries()))
    print('timezones', len(cfg.get_timezones()))
    print('alert technologies', len(cfg.get_alert_technologies()))
    print('nocs', len(cfg.get_nocs()))
    print('device types', len(cfg.get_device_types()))

    # Focus on a specific tenant.
    tenant = ormp.tenant(TENANT_ID)

    print('List the integrations on tenant', TENANT_ID)
    integs = tenant.integrations()
    group = integs.itypes()
    found = group.search()
    print(found['totalResults'], 'integration types')
    for i in found['results']:
        print(i)

    print('Define new custom integrations on', TENANT_ID)
    group = integs.instances()
    for atype in ('OAUTH2', 'BASIC'):
        newcint = group.mkCustom(
            display_name='Example %s integration' % atype,
            inbound_auth_type=atype
        )
        print(newcint)
        # uncomment the following lines to actually create the integration.
        # if tenant.is_client():
        #     resp = group.create('CUSTOM', newcint)
        #     group.redact_response(resp)
        #     print(resp)

    found = group.search()
    print(found['totalResults'], 'integration instances')
    # "found" contains a complete description of each integration but let's
    # pull them individually anyway and assert that this gives same result.
    for i in found['results']:
        print('...', i['id'], i['integration']['id'],
              '"' + i.get('displayName', '<no name>') + '"')
        direct = group.get(i['id'])
        assert direct == i

    # Retrieve the agent installation script for this client. The string
    # that OpsRamp returns will contain keys for the client so just print
    # its length and first line to show that we got something.
    if tenant.is_client():
        print('agent installation script for client', TENANT_ID)
        agent_script = tenant.get_agent_script()
        print('length', len(agent_script))
        print(agent_script.split('\n')[0])
    else:
        print('List the clients of tenant', TENANT_ID)
        group = tenant.clients()
        for c in group.get():
            print(c)
            resp = group.get(c['uniqueId'])
            print('createdBy', resp['createdBy'])
        print('Exercise the create-client code')
        cdef = group.mkClient(
            name='test client 99',
            address='Death Valley',
            time_zone='America/Los_Angeles',
            country='United States')
        print(cdef)
        # uncomment these lines to actually create the client.
        # resp = group.create(cdef)
        # print(resp)

    print('List the monitoring templates on tenant', TENANT_ID)
    monitoring = tenant.monitoring()
    templates = monitoring.templates()
    resp = templates.search()
    print(resp['totalResults'], 'templates')
    for t in resp['results']:
        print('...', t['name'])

    # list the RBA script categories and find or create the one we want.
    print('List the RBA categories on tenant', TENANT_ID)
    rba = tenant.rba()
    group = rba.categories()
    clist = group.get()
    print(len(clist), 'categories')
    for c in clist:
        print(c)
        if c['name'] == CATEGORY_NAME:
            cid = c['id']
            break
    else:
        resp = group.create(CATEGORY_NAME)
        cid = resp['id']

    print('Scripts in category', cid)
    cobj = group.category(cid)
    slist = cobj.get()
    print(len(slist), 'scripts')
    for s in slist:
        print('...', s['id'], s['name'])
        direct = cobj.get(s['id'])
        assert s == direct

    # Create a new RBA script in this category, with one parameter. You can
    # see from the "payload" that this gets passed to the script as $1
    p1 = cobj.mkParameter(
        name='venue',
        description='Where am I today?',
        datatype='STRING'
    )
    print('Parameter definition struct')
    print(p1)
    s1 = cobj.mkScript(
        name='Hello <venue>',
        description='Stereotypical rock star intro',
        platforms=['LINUX'],
        execution_type='COMMAND',
        payload='echo "hello $1"',
        parameters=[p1]
    )
    print('Script definition struct')
    print(s1)
    # uncomment these lines to actually create the script.
    # resp = cobj.create(s1)
    # print(resp)

    print('Management policies on tenant', TENANT_ID)
    group = tenant.policies()
    plist = group.get()
    print(len(plist), 'policies')
    for p in plist:
        rules = p['rules']
        actions = p['actions']
        print('...', p['id'], p['uid'], p['name'],
              'rules', len(rules),
              'actions', len(actions))
        for r in rules:
            print('...... rule', r)
        for a in actions:
            print('...... action', a['action'])
        # plist contains a complete description of each policy
        # but let's pull them individually anyway and assert that
        # this gives the same result.
        direct = group.get(p['id'])
        print(direct)
        assert p == direct

    print('Credential sets on tenant', TENANT_ID)
    cs = tenant.credential_sets()
    resp = cs.get()
    print(resp['totalResults'], 'credential sets')
    for i in resp['results']:
        print(i)

    print('Discovery Profiles on tenant', TENANT_ID)
    if tenant.is_client():
        discovery = tenant.discovery()
        profiles = discovery.get()
        print(len(profiles), 'profiles')
        for profile in profiles:
            id = profile['id']
            name = profile['name']
            print("Profile ID: %s name %s\n" % (id, name))
            # Get profile by ID
            this_profile = discovery.get(id)
            print("Profile %s: %s\n" % (id, str(this_profile)))
            this_profile = discovery.search(name)
            print("Profile %s: %s\n" % (name, str(this_profile)))


if __name__ == "__main__":
    main()
