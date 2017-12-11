# -*- coding: utf-8 -*-
import os
import requests
import pprint
import argparse
import sys

OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

# app = Flask(__name__)
basetoken = "bearer "
regions = {
    '米国南部': 'https://api.ng.bluemix.net',
    'シドニー': 'https://api.au-syd.bluemix.net',
    'ドイツ': 'https://api.eu-de.bluemix.net',
    '英国': 'https://api.eu-gb.bluemix.net'
}
pp = pprint.PrettyPrinter(indent=4)


def getToken():
    # get login token
    apikey = os.getenv("APIKEY")
    if (apikey is None):
        print(apikey)
        return None
    else:
        s = requests.session()
        loginUrl = "https://login.ng.bluemix.net/UAALoginServerWAR/oauth/token"
        payload = "grant_type=password&username=apikey&password=" + apikey
        headers = {
            'authorization': "Basic Y2Y6",
            'accept': "application/json",
            'content-type': "application/x-www-form-urlencoded",
            'cache-control': "no-cache"
            }
        response = s.post(loginUrl, data=payload, headers=headers)
        t = response.json()
        # token = t['access_token']
        return t.get('access_token')


def getOrganization(organization_name: str, baseurl: str):
    orgs = {}
    next_url = '/v2/organizations?ressults-per-page=50'
    while True:
        apiurl = baseurl + next_url
        s = requests.session()
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': securitytoken.encode('utf-8')
        }
        s.headers = headers
        response = s.get(apiurl)
        data = response.json()
        if data.get('resources'):
            for entry in data['resources']:
                label = entry['entity']['name']
                guid = entry['metadata']['guid']
                orgs[label] = guid
            next_url = data['next_url']
            if (data['next_url'] is None):
                break
        else:
            break
    return orgs.get(organization_name)  # organization_guid


def getSpace(space_name: str, organization_name: str):
    # spaces = {}
    spaces = {}
    spaces[space_name] = []
    for region, baseurl in regions.items():
        orgId = getOrganization(organization_name, baseurl)
        if orgId:
            # print(orgId)
            next_url = '/v2/organizations/' + orgId + '/spaces' + \
                '?ressults-per-page=50'
            print('space searching... ' + region, end="")
            apiurl = baseurl + next_url
            s = requests.session()
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': securitytoken.encode('utf-8')
            }
            s.headers = headers
            response = s.get(apiurl)
            data = response.json()
            # pp.pprint(data)
            # print(space_name + ':' + organization_name + ':' + region)
            if data.get('resources'):
                for entry in data['resources']:
                    label = entry['entity']['name']
                    if space_name == label:
                        if entry['metadata'].get('guid'):
                            guid = entry['metadata']['guid']
                            spaces[space_name].append({'guid': guid, 'baseurl': baseurl, 'region': region})
                            # spaces[label] = guid
                            # print(spaces)
                    # print('entry not found : ' + label)
                            print(OKBLUE + ' ✔' + ENDC)
                # print(FAIL + ' X' + ENDC)
            else:
                print(FAIL + ' X' + ENDC)
            # print(spaces)
        # else:
            # print("organization is not found")
    # print(spaces)
    return spaces.get(space_name)  # : dict


def removeservivce(app_id: str, baseurl: str):
    # services = {}
    next_url = '/v2/apps/' + app_id + '/summary'
    apiurl = baseurl + next_url
    s = requests.session()
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': securitytoken.encode('utf-8')
    }
    s.headers = headers
    response = s.get(apiurl)
    data = response.json()
    # print(data)
    if data.get('services'):
        for entry in data['services']:
            label = entry['name']
            guid = entry['guid']
            print("   " + WARNING + label + ENDC + " : " + guid, end='')
            # service binding を取得する
            next_url = '/v2/apps/' + app_id + '/service_bindings?q=service_instance_guid%3A' + guid
            # print(next_url)
            apiurl = baseurl + next_url
            response = s.get(apiurl)
            data = response.json()
            # print(data)
            for entry in data.get('resources'):
                next_url = entry['metadata']['url']
                # print(next_url)
                apiurl = baseurl + next_url
                response = s.delete(apiurl)
                if response.status_code == 204:
                    print(OKBLUE + ' ✔ ' + ENDC)
                else:
                    print(FAIL + ' X ' + ENDC)
    else:
        print("   " + OKBLUE + ' ✔ ' + ENDC + "bind service not found")
    return True


def deleteApps(organization_name: str, space_name: str):

    for spaceInfo in getSpace(space_name, organization_name):
        # print(spaceInfo)
        if spaceInfo:
            spaceId = spaceInfo['guid']
            region = spaceInfo['region']
            baseurl = spaceInfo['baseurl']
            print('service searching: ' + region)
            apps = {}
            next_url = '/v2/apps?q=space_guid%3A' + spaceId
            # print(next_url)
            while True:
                apiurl = baseurl + next_url
                s = requests.session()
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': securitytoken.encode('utf-8')
                }
                s.headers = headers
                response = s.get(apiurl)
                data = response.json()
                # print(data)
                if data.get('resources'):
                    for entry in data['resources']:
                        label = entry['entity']['name']
                        guid = entry['metadata']['guid']
                        apps[label] = {'guid': guid, 'region_url': baseurl, 'region': region}
                    next_url = data['next_url']
                    if (data['next_url'] is None):
                        break
                else:
                    break

            # pp.pprint(apps)
            for appName, value in apps.items():
                print('-> ' + region + ' : ' +appName + ' : ' + OKGREEN+value['guid']+ENDC + ' ')
                removeservivce(value['guid'], value['region_url'])
                next_url = '/v2/apps/' + value['guid']
                appurl = value['region_url'] + next_url
                response = s.delete(appurl)
                if response.status_code == 204:
                    print(WARNING + '    ✔ ' + ENDC, end='')
                    print('app delete')

                else:
                    err = response.json()
                    print(FAIL + '    X ' + ENDC, end='')
                    print('app delete :' + err['description'])

    return True


def removekeys(servie_guid, baseurl):
    next_url = '/v2/service_keys?q=service_instance_guid%3A' + servie_guid
    apiurl = baseurl + next_url
    keys = {}
    # print(apiurl)
    s = requests.session()
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': securitytoken.encode('utf-8')
    }
    s.headers = headers
    response = s.get(apiurl)
    data = response.json()
    # print(data)
    if data.get('resources'):
        for entry in data['resources']:
            label = entry['entity']['name']
            guid = entry['metadata']['guid']
            keys[label] = {'guid': guid, 'region_url': baseurl}

    # 取得したcredectialのkeyを削除する
    # print(keys)
    for keyName, v in keys.items():
        print('    ' + keyName + ':' + v['guid'])
        keyurl = '/v2/service_keys/' + v['guid']
        apiurl = v['region_url'] + keyurl
        response = s.delete(apiurl)
        # data = response.json
        if response.status_code == 204:
            print(WARNING + '    ✔ ' + ENDC, end='')
            print('Key delete')
        else:
            err = response.json()
            print(FAIL + '    X ' + ENDC, end='')
            print('Key delete :' + err['description'])

    return True


def deleteServices(organization_name: str, space_name: str):

    for spaceInfo in getSpace(space_name, organization_name):
        # print(spaceInfo)
        if spaceInfo:
            spaceId = spaceInfo['guid']
            region = spaceInfo['region']
            baseurl = spaceInfo['baseurl']
            print('service searching: ' + region)
            services = {}
            next_url = '/v2/spaces/' + spaceId + '/service_instances'
            while True:
                apiurl = baseurl + next_url
                # print(apiurl)
                s = requests.session()
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': securitytoken.encode('utf-8')
                }
                s.headers = headers
                response = s.get(apiurl)
                data = response.json()
                # print(data)
                if data.get('resources'):
                    for entry in data['resources']:
                        label = entry['entity']['name']
                        guid = entry['metadata']['guid']
                        services[label] = {'guid': guid, 'region_url': baseurl, 'region': region}
                    next_url = data['next_url']
                    if (data['next_url'] is None):
                        break
                else:
                    break
            # pp.pprint(services)

            for serviceName, value in services.items():
                print('-> ' + region + ' : ' + serviceName + ' : ' + OKGREEN+value['guid']+ENDC + ' ')
                removekeys(value['guid'], value['region_url'])
                next_url = '/v2/service_instances/' + value['guid'] + '?accepts_incomplete=true'
                appurl = value['region_url'] + next_url
                # 202 : async=true,accepts_incomplete の場合の返り値
                response = s.delete(appurl)
                # print(response.status_code)
                if (response.status_code == 204 or response.status_code == 202):
                    print(WARNING + '    ✔ ' + ENDC, end='')
                    print('service delete')

                else:
                    err = response.json()
                    # 失敗した場合には Keyがあるか routeがあるかのどちらか
                    print(FAIL + '    X ' + ENDC, end='')
                    print('service delete :' + err['description'])


def main():
    parser = argparse.ArgumentParser(description="description goes here")
    parser.add_argument("-s", type=str, help="target space", required=True)
    parser.add_argument("-o", type=str, help="target organization",
                        required=True)
    command_arguments = parser.parse_args()
    deleteApps(command_arguments.o, command_arguments.s)
    deleteServices(command_arguments.o, command_arguments.s)


if __name__ == "__main__":
    if (not os.getenv("APIKEY")):
        print('please set enrironment APIKEY.')
        sys.exit()
    else:
        securitytoken = basetoken + getToken()
        main()
