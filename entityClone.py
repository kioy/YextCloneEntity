#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
entityClone.py: Clone/Update an entity
Usage: entityClone.py <options>

Options:
  -h                                this help
  -a --api-key <api-key>            Yext API Key
  -i --id <id>                      Entity ID of Original Data
  -o --out <id>                     Entity ID of Clone Entity
  -g --debug                        Pring debugging information
  -w --overwrite                    Update existing entity

Mail bug reports and suggestion to : Yukio Y <unknot304 AT gmail.com>

Example: entityClone.py -a <key> -i <entity id> -o <entity id> -g
"""
from __future__ import print_function
import sys, os, errno
import argparse
import getpass

import time
import json
import requests
import logging

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update an Entity')
    parser.add_argument(
        '-a', '--api-key',
        type = str,
        dest = 'api_key',
        required = True,
        help = 'Yext API Key'
	)
    parser.add_argument(
        '-i', '--id',
        type = str,
        dest = 'orig_entity_id',
        required = True,
        help = 'Entity Id of Original'
	)
    parser.add_argument(
        '-o', '--out',
        type = str,
        dest = 'clone_entity_id',
        required = True,
        help = 'Entity Id of Clone'
        )
    parser.add_argument(
        '-w', '--overwrite',
        action = 'store_true',
        dest = 'overwrite',
        default = False,
        required = False,
        help = 'Overwrite existing entity'
        )
    parser.add_argument(
        '-g', '--debug',
        action='store_true',
        dest = 'debug',
        default = False,
        required = False,
        help = 'Pring debugging information'
	)

    args = parser.parse_args()

    s = requests.Session()
    s.headers.update({'Referer': 'unknot304.com/entityClone',
                      'Accept': 'application/json',
                      'Content-Type': 'application/json; charset=utf-8'})

    #get original entity
    call_url = 'https://api.yext.com/v2/accounts/me/entities/'+args.orig_entity_id+'?v=20210301&api_key='+args.api_key
    try:
        response = s.get(call_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error",e)
        print(json.dumps(response.json(), indent=4, ensure_ascii=False), file=sys.stderr)
        sys.exit()

    response.encoding = response.apparent_encoding
    data = response.json()
    clone_data = data['response']

    if args.debug:
        print('Retrived original entity: '+args.orig_entity_id)
        print(json.dumps(clone_data, indent=4, ensure_ascii=False), file=sys.stderr)
    

    #revise meta info for clone
    clone_data['meta']['id'] = args.clone_entity_id
    original_primary_language = clone_data['meta']['language']
    original_entity_type = clone_data['meta']['entityType']
    del clone_data['meta']['accountId']
    del clone_data['meta']['timestamp']
    del clone_data['meta']['uid']
    del clone_data['meta']['entityType']

    if args.debug:
        print('Revised meta info for creating an entity: '+args.clone_entity_id)
        print(json.dumps(clone_data, indent=4, ensure_ascii=False), file=sys.stderr)


    #clone entity with primary language data
    call_url_create = 'https://api.yext.com/v2/accounts/me/entities?v=20210301&api_key='+args.api_key+'&entityType='+original_entity_type+'&format=markdown'
    call_url_update = 'https://api.yext.com/v2/accounts/me/entities/'+args.clone_entity_id+'?v=20210301&api_key='+args.api_key+'&entityType='+original_entity_type+'&format=markdown'
    try:
        if args.overwrite:
            del clone_data['meta']['folderId']
            del clone_data['meta']['id']
            response = s.put(call_url_update, json.dumps(clone_data))
        else:
            response = s.post(call_url_create, json.dumps(clone_data))
            
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error",e)
        print(json.dumps(response.json(), indent=4, ensure_ascii=False), file=sys.stderr)
        sys.exit()

    if args.debug:
        print('Created: '+args.clone_entity_id)


    #get profile data for multi-language entity
    call_url = 'https://api.yext.com/v2/accounts/me/entityprofiles/'+args.orig_entity_id+'?v=20210301&api_key='+args.api_key
    try:
        response = s.get(call_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error",e)
        print(json.dumps(response.json(), indent=4, ensure_ascii=False), file=sys.stderr)
        sys.exit()

    response.encoding = response.apparent_encoding
    data = response.json()
    clone_profile_data = data['response']['profiles']

    if args.debug:
        print('Retrieved Multi-Language Proilfes')

    
    # upserts each language data except primary language (it already created)
    for profile in clone_profile_data:
        profile_language = profile['meta']['language']
        if profile_language == original_primary_language:
            continue
        if args.debug:
            print("Updating profile data...")
            print(json.dumps(profile, indent=4, ensure_ascii=False), file=sys.stderr)

        call_url = 'https://api.yext.com/v2/accounts/me/entityprofiles/'+args.clone_entity_id+'/'+profile_language+'?v=20210301&api_key='+args.api_key+'&entityType='+original_entity_type+'&format=markdown'
        try:
            del profile['meta']['accountId']
            del profile['meta']['timestamp']
            del profile['meta']['uid']
            del profile['meta']['entityType']
            del profile['meta']['folderId']
            del profile['meta']['id']
            response = s.put(call_url, json.dumps(profile))
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print("Error",e)
            print(json.dumps(response.json(), indent=4, ensure_ascii=False), file=sys.stderr)
            sys.exit()
        
    

    
#    if success == "ZERO_RESULTS":
#        number_of_locations = 0
#    elif success == "OK":
#        number_of_locations = len(data['results'])
#    else:
#        print("Error!", file=sys.stderr)
#        sys.exit(1)
#


# get next locations with page_token
#    page_token = data ['next_page_token']
#    while page_token:
#        q['pagetoken'] = page_token
#        response = s.get(call_url, params=q)
#        data = response.json()
#
#        success = data ['staus']
#        if success != "OK":
#            print("Error status:", success, file=sys.stderr)
#            sys.exit(1)
#
#        page_token = data ['next_page_token']
#
        # if args.detail:
#        print(json.dumps(data, indent=4), file=sys.stderr)
