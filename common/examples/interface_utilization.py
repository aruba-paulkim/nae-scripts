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

Manifest = {
    'Name': 'interface_utilization_monitor',
    'Description': '',
    'Version': '1.0',
    'Author': 'Paul Kim'
}


ParameterDefinitions = {
    'monitor_interface_id': {
        'Name': 'Monitor Interface Id',
        'Description': 'Interface to be monitored',
        'Type': 'string',
        'Default': '1/5/1'
    },
    'backup_uplink_interface_id': {
        'Name': 'Backup Uplink Interface Id',
        'Description': 'backup uplink Interface',
        'Type': 'string',
        'Default': '1/5/3'
    },
    'backup_uplink_interface_ip': {
        'Name': 'Backup Uplink Interface ip',
        'Description': 'backup uplink Interface',
        'Type': 'string',
        'Default': '20.1.1.1'
    },
    'target_interface_id': {
        'Name': 'Target Interface Id',
        'Description': 'Target Interface',
        'Type': 'string',
        'Default': '1/5/7'
    },
    'target_interface_ip': {
        'Name': 'Target Interface ip',
        'Description': 'backup uplink Interface',
        'Type': 'string',
        'Default': '100.1.2.2'
    },
    'utilization_threshold_up': {
        'Name': 'Utilization Threshold TX+RX',
        'Description': 'utilization_threshold',
        'Type': 'float',
        'Default': '170'
    },
    'utilization_threshold_down': {
        'Name': 'Utilization Threshold TX+RX',
        'Description': 'utilization_threshold',
        'Type': 'float',
        'Default': '130'
    }
}


class Agent(NAE):

    def __init__(self):
        uri10 = '/rest/v1/system/interfaces/{}?attributes=rate_statistics.utilization'
        self.m10 = Monitor(uri10, 'Interface Utilization', [self.params['monitor_interface_id']])
        self.r10 = Rule('Rule for Monitor Interface Utilization')
        self.r10.condition('{} >= {}', [self.m10, self.params['utilization_threshold_up']])
        self.r10.action(self.threshold_over_callback)
        self.r10.clear_condition('{} < {}', [self.m10, self.params['utilization_threshold_down']])
        self.r10.clear_action(self.threshold_clear_callback)

    def threshold_over_callback(self, event):
        try:
            self.set_alert_level(AlertLevel.CRITICAL)
            ActionSyslog('ActionSyslog : threshold_over_callback')
            ActionCLI("show logging -r -n 10")
            ActionCLI("config\nclass ip PBR\n10 match any {} any count\nexit\npbr-action-list PBR\n10 nexthop {}\nexit\npolicy PBR\n10 class ip PBR action pbr PBR\nexit\ninterface {}\napply policy PBR routed-in\nexit\nexit", [self.params['target_interface_ip'], self.params['backup_uplink_interface_ip'], self.params['target_interface_id']])
        except Exception as e:
            ActionSyslog("[ERROR] threshold_over_callback: {}".format(str(e)))

    def threshold_clear_callback(self, event):
        try:
            self.set_alert_level(AlertLevel.NONE)
            ActionSyslog('ActionSyslog : threshold_clear_callback')
            ActionCLI("show logging -r -n 10")
            ActionCLI("config\ninterface {}\nno apply policy PBR routed-in\nexit\nno policy PBR\nno pbr-action-list PBR\nno class ip PBR\nexit", [self.params['target_interface_id']])
        except Exception as e:
            ActionSyslog("[ERROR] threshold_clear_callback: {}".format(str(e)))

