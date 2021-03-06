
# encoding = utf-8

import os
import sys
import time
import datetime
import json

'''
    IMPORTANT
    Edit only the validate_input and collect_events functions.
    Do not edit any other part in this file.
    This file is generated only once when creating the modular input.
'''
'''
# For advanced users, if you want to create single instance mod input, uncomment this method.
def use_single_instance_mode():
    return True
'''

def validate_input(helper, definition):
    """Implement your own validation logic to validate the input stanza configurations"""
    pass

def collect_events(helper, ew):
    """Implement your data collection logic here"""

    # The following examples get the arguments of this input.
    # Note, for single instance mod input, args will be returned as a dict.
    # For multi instance mod input, args will be returned as a single value.
    opt_airlock_server_fqdn = helper.get_global_setting('airlock_server_fqdn')
    opt_airlock_rest_api_port = helper.get_global_setting('airlock_rest_api_port')
    opt_airlock_rest_api_key = helper.get_global_setting('airlock_rest_api_key')
    #opt_verify_remote_tls_certificate = helper.get_global_setting('verify_remote_tls_certificate')
    opt_execution_types_to_collect = helper.get_arg('execution_types_to_collect')
    opt_delete_existing_checkpoint = helper.get_arg('delete_existing_checkpoint')
    if opt_delete_existing_checkpoint is True:
        helper.delete_check_point("checkpoint")
        helper.log_debug("Existing checkpoint deleted, now exiting. Disable the Delete Existing Checkpoint option to index logs")
        exit()
    # The following examples get options from setup page configuration.
    # get proxy setting configuration
    proxy_settings = helper.get_proxy()
    # get account credentials as dictionary
    #account = helper.get_user_credential_by_username("username")
    #account = helper.get_user_credential_by_id("account id")
    # get global variable configuration
    #global_userdefined_global_var = helper.get_global_setting("userdefined_global_var")
    # get checkpoint
    checkpoint = helper.get_check_point("checkpoint")

    url = "https://"+opt_airlock_server_fqdn +":"+opt_airlock_rest_api_port+"/v1/logging/exechistories"
    try:
        helper.log_debug("Checkpoint value in Splunk is:" + checkpoint)
    except:
        helper.log_debug("Checkpoint appears to be empty")
    # The following examples send rest requests to some endpoint.
    if checkpoint is None:
        helper.log_debug("No historical checkpoint found, obtaining restart checkpoint from Airlock") 

        response = helper.send_http_request(url, method="POST", parameters=None, payload={"type":opt_execution_types_to_collect},headers={"X-ApiKey":opt_airlock_rest_api_key}, cookies=None, verify=True, cert=None,timeout=None, use_proxy=True)
        response.raise_for_status()
        r_json = response.json()        
        if not 'response' in r_json or len(r_json['response']['exechistories']) == 0: #If there are no results we don't need to write anything or do much
            helper.log_info("Something went wrong sending the request to the Airlock Server, please check connectivity and your API key. Unable to get initial checkpoint.")
            exit() #Stop here because we can't continue
            
        else:
            r_json = response.json()
            helper.log_debug(r_json)
            checkpoint = r_json['response']['exechistories'][-1]['checkpoint']
            #Write the events to the specified index
            event = helper.new_event(source=url, sourcetype="airlock:exechistories", index=helper.get_output_index(), data=json.dumps(r_json['response']['exechistories']))
            #replace hardcoded index with index=helper.get_output_index()
            # save checkpoint
            helper.log_debug("Saving checkpoint to Splunk:" + checkpoint)
            helper.save_check_point("checkpoint", checkpoint)

    else:
        helper.log_debug("Historical checkpoint found:" + checkpoint)
        try:
            response = helper.send_http_request(url, method="POST", parameters=None, payload={"checkpoint":checkpoint,"type":opt_execution_types_to_collect},headers={"X-ApiKey":opt_airlock_rest_api_key}, cookies=None, verify=True, cert=None,timeout=None, use_proxy=True)
            response.raise_for_status()
            r_json = response.json()
        except:
            helper.log_info("Something went wrong sending the request to the Airlock Server, please check connectivity and your API key for validity.")
            exit() #If the request is unable to be sent we should quit here
            
        if not 'response' in r_json or len(r_json['response']['exechistories']) == 0: #If there are no results we don't need to write anything or do much
            helper.log_debug("no results, nothing to do")
        else:    
            helper.log_debug("there are results to parse")
            helper.log_debug(r_json)
            #Write the events to the specified index
            for i in r_json['response']['exechistories']:
                event = helper.new_event(source=url, sourcetype="airlock:exechistories", index=helper.get_output_index(), data=json.dumps(i))
                ew.write_event(event)
            index=helper.get_output_index()
            helper.log_debug("index is" + index)
            #Set latest checkpoint
            checkpoint = r_json['response']['exechistories'][-1]['checkpoint']
            # save checkpoint
            helper.log_info("Saving checkpoint to Splunk:" + checkpoint)
            helper.save_check_point("checkpoint", checkpoint)



