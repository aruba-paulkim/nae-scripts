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
    'Name': 'interface_link_state_monitor_for_EEM',
    'Description': 'interface_link_state_monitor_for_EEM',
    'Version': '1.0',
    'Author': 'Paul.Kim'
}

ParameterDefinitions = {
    'monitor_interface_id': {
        'Name': 'Monitor Interface Id',
        'Description': '',
        'Type': 'string',
        'Default': '1/1/1'
    },
    'backup_interface_id': {
        'Name': 'Backup Interface Id',
        'Description': '',
        'Type': 'string',
        'Default': '1/1/2'
    }
}


class Agent(NAE):

    def __init__(self):
        # Interface status
        uri1 = '/rest/v1/system/interfaces/{}?attributes=link_state'
        self.m1 = Monitor(uri1,'Interface Link status',[self.params['monitor_interface_id']])
        self.r1 = Rule('Link Went Down')
        self.r1.condition('transition {} from "up" to "down"', [self.m1])
        self.r1.action(self.action_interface_down)

        # Reset agent status when link is up
        self.r2 = Rule('Link Came UP')
        self.r2.condition('transition {} from "down" to "up"', [self.m1])
        self.r2.action(self.action_interface_up)


    def action_interface_down(self, event):
        self.logger.debug("================ Down ================")
        ActionSyslog('Interface {} Link gone down', [self.params['monitor_interface_id']])
        ActionCLI("show interface {}", [self.params['monitor_interface_id']])
        ActionCLI("show interface {}", [self.params['backup_interface_id']])
        # backup interface going up
        ActionCLI("configure\ninterface {}\nno shutdown\nend", [self.params['backup_interface_id']])
        self.logger.debug("================ /Down ================")


    def action_interface_up(self, event):
        self.logger.debug("================ Up ================")
        ActionSyslog('Interface {} Link came up', [self.params['monitor_interface_id']])
        ActionCLI("show interface {}", [self.params['monitor_interface_id']])
        ActionCLI("show interface {}", [self.params['backup_interface_id']])
        # backup interface going down
        ActionCLI("configure\ninterface {}\nshutdown\nend", [self.params['backup_interface_id']])
        self.logger.debug("================ /Up ================")
