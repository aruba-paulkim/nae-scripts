# -*- coding: utf-8 -*-
#
# (c) Copyright 2018 Hewlett Packard Enterprise Development LP
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

import requests, json

Manifest = {
    'Name': 'configuration_change_LineMessager',
    'Description': 'Agent to alert user when configuration changes and diff of configuration changes.'
                   'An LineMessager notification with the diff url is sent whenever the configuration changes.',
    'Version': '1.0',
    'Author': 'Paul.Kim'}

ParameterDefinitions = {
    'channel_id': {
        'Name': 'Line Channel ID',
        'Description': '',
        'Type': 'string',
        'Default': '',
        'Encrypted': True
    },
    'channel_secret': {
        'Name': 'Line Channel Secret',
        'Description': '',
        'Type': 'string',
        'Default': '',
        'Encrypted': True
    }
}


class Agent(NAE):

    def __init__(self):

        uri = '/rest/v1/system?attributes=last_configuration_time'
        rate_uri = Rate(uri, '10 seconds')
        self.monitor = Monitor(rate_uri, 'Rate of last configuration time')
        self.rule = Rule('Configuration change')
        self.rule.condition('{} > 0', [self.monitor])
        self.rule.action(self.calculate_base_config_checkpoint)
        self.rule.clear_condition('{} == 0', [self.monitor])
        self.rule.clear_action(self.calculate_config_diff)


    def calculate_base_config_checkpoint(self, event):

        try:
            r = requests.get(HTTP_ADDRESS + '/rest/v1/configlist', verify=True, proxies={'http': None, 'https': None})
            r.raise_for_status()
            configlist = r.json()
            self.variables['base_checkpoint'] = configlist[-1]['name']
        except Exception as e:
            ActionSyslog("[configuration_change_LineMessager] calculate_base_config_checkpoint Could not get checkpoint list: {}".format(str(e)))


    def calculate_config_diff(self, event):

        if 'base_checkpoint' in self.variables:
            base_checkpoint = self.variables['base_checkpoint']
        else:
            base_checkpoint = 'startup-config'

        try:
            r = requests.get(HTTP_ADDRESS + '/rest/v1/config/diff/%s/running-config' % base_checkpoint, verify=True, proxies={'http': None, 'https': None})
            r.raise_for_status()
            description = r.json()['output']

            # Making diff url
            diff_url = self.get_diff_url(description)

            # Send Notification by LineMessager
            line = LineMessager(self.params['channel_id'], self.params['channel_secret'], diff_url)

        except Exception as e:
            ActionSyslog("[configuration_change_LineMessager] calculate_config_diff Error creating notification: {}".format(str(e)))


    def get_diff_url(self, diff):

        diff_api = "http://apollo89.com/aruba/hash.html"
        headers = {"Content-Type":"application/x-www-form-urlencoded"}
        data = {"data":diff}
        response = requests.post(diff_api, headers=headers, data=data, verify=False, timeout=10)
        if response.status_code == 200 :
            diff_url = response.text
        else :
            ActionSyslog("[configuration_change_LineMessager] get_diff_url status code : " + str(response.status_code)) 
            ActionSyslog("[configuration_change_LineMessager] get_diff_url header: %s" % response.headers)
            ActionSyslog("[configuration_change_LineMessager] get_diff_url text: %s" % response.text)

        ActionSyslog("[configuration_change_LineMessager] get_diff_url url : "+diff_url)
        return diff_url



class LineMessager:

    def __init__(self, channel_id, channel_secret, diff_url):

        self.channel_id = str(channel_id)
        self.channel_secret = str(channel_secret)
        self.diff_url = str(diff_url)

        self.access_token = ""
        self.token_type = ""

        self.get_access_token()
        self.send_message_broadcast("config changed! : " + diff_url)


    def get_access_token(self):

        url_accessToken = "https://api.line.me/v2/oauth/accessToken"
        headers = {"Content-Type":"application/x-www-form-urlencoded"}
        params = {"grant_type":"client_credentials",
                    "client_id":self.channel_id, "client_secret":self.channel_secret}
        response = requests.post(url_accessToken, headers=headers, params=params, verify=True, timeout=10)
        if response.status_code == 200 :
            tmp = json.loads(response.text)
            self.token_type = tmp['token_type']
            self.access_token = tmp['access_token']
        else :
            raise Exception("[configuration_change_LineMessager] Fail to get_access_token!")
        

    def send_message_broadcast(self, message):

        url_broadcast = "https://api.line.me/v2/bot/message/broadcast"
        headers = {"Content-Type":"application/json", "Authorization": self.token_type+" "+ self.access_token}
        data = {"messages":[{"type":"text","text":message}]}
        
        response = requests.post(url_broadcast, headers=headers, data=json.dumps(data), verify=True, timeout=10)
        if response.status_code == 200 :
            print("send_message_broadcast complete")
        else :
            raise Exception("[configuration_change_LineMessager] Fail to send_message_broadcast!")



