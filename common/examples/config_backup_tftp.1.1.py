# -*- coding: utf-8 -*-
#
# (c) Copyright 2017-2018 Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the License for the
# specific language governing permissions and limitations
# under the License.

import time
import datetime as dt
from requests import get

Manifest = {
    'Name': 'config_backup_tftp',
    'Description': '',
    'Version': '1.1',
    'Author': 'Paul Kim'
}


ParameterDefinitions = {
    'tftp_server_address': {
        'Name': 'IP address or hostname of the TFTP server',
        'Description': 'Enter the hostname or IP address of the TFTP server'
                       ' to which the running-config is to be copied when the'
                       ' configuration changes.',
        'Type': 'string',
        'Default': '',
    },
    'tftp_server_vrf': {
        'Name': 'VRF to reach the TFTP server',
        'Description': 'Enter the vrf through which the TFTP server '
                       'can be reached.',
        'Type': 'string',
        'Default': 'mgmt'
    },
    'tftp_configuration_format': {
        'Name': 'Format in which the configuration is copied to the '
                'TFTP server',
        'Description': 'Enter the format in which the configuration is '
                       'to be copied to the TFTP server. Possible values '
                       'are cli and json.',
        'Type': 'string',
        'Default': 'cli'
    },
    'tftp_config_file_name_prefix': {
        'Name': 'Prefix for the file name for configuration during'
                ' TFTP process',
        'Description': 'Enter the prefix for the filename in which the'
                       ' configuration is to be stored on the '
                       'TFTP server. Timestamp will be '
                       'attached  to the prefix in the filename.',
        'Type': 'string',
        'Default': ''
    },
    'config_backup_period': {
        'Name': 'config backup period(minutes)',
        'Description': '1day : 1440 minute / 7days : 10080minutes / 30days : 43200 minutes ',
        'Type': 'integer',
        'Default': '1440'
    }
}


def rest_get(url):
    return get(HTTP_ADDRESS + url, verify=False, proxies={'http': None, 'https': None})


class Agent(NAE):

    def __init__(self):
        uri = '/rest/v1/system?attributes=last_configuration_time'
        rate_uri = Rate(uri, '10 seconds')
        self.monitor = Monitor(rate_uri, 'Rate of last configuration time')
        self.r1 = Rule('last configuration time')
        self.r1.condition('every {} minutes', [self.params['config_backup_period']])
        self.r1.action(self.action_tftp_backup)


    def action_tftp_backup(self, event):
        print("===== start action_tftp_backup ================")
        x = dt.datetime.now()
        now_datetime = x.strftime("%Y%m%d%H%M%S")

        r = rest_get('/rest/v1/system?attributes=mgmt_intf_status')
        r.raise_for_status()
        hostname = r.json()['mgmt_intf_status']['hostname']


        cmd = "copy running-config tftp://%s/%s-%s-%s %s vrf %s" % (self.params['tftp_server_address'], 
            self.params['tftp_config_file_name_prefix'], hostname,
            now_datetime, self.params['tftp_configuration_format'], self.params['tftp_server_vrf'])
        print("action_tftp_backup : " + cmd)
        ActionCLI(cmd)
        print("===== end   action_tftp_backup ================")


