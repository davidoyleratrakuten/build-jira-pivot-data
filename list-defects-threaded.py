#!/usr/bin/env python3

import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor

# Set defined configuration file for all program variables
CONFIG_FILE = "config.json"

def make_request(url, auth, headers, params):
    try:
        response = requests.get(url, auth=auth, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to make a request: {e}")
        exit(1)

def search_defects(issue):
    username = config["username"]
    api_token = config["api_token"]
    base_url = config["base_url"]
    project_key = config["project_key"]
    feature_field_id = config["feature_field_id"]
    severity_field_id = config["severity_field_id"]
    output_file = config["output_file"]

    # Create headers with basic authentication
    headers = {"Content-Type": "application/json"}

    key = issue['key']
    jql_query = f'key = {key}'
    fields = f'key, customfield_{feature_field_id}, customfield_{severity_field_id}'

    key_params = {
        'jql': jql_query,
        'fields': fields
    }
    keydata_url = f'{base_url}/search'
    keydata_response = make_request(keydata_url, (username, api_token), headers, key_params)

    key = keydata_response['issues'][0]['key']
    severity = keydata_response['issues'][0]['fields'][f'customfield_{severity_field_id}']['value']

    feature_count = len(keydata_response['issues'][0]['fields'][f'customfield_{feature_field_id}'])

    for j in range(feature_count):
        feature = keydata_response['issues'][0]['fields'][f'customfield_{feature_field_id}'][j]['value']
        with open(output_file, "a") as ofile:
            ofile.write(f"{feature}\t{key}\t{severity}\n")

def process_issue(issue):
    search_defects(issue)

def search_issues():
    # Read values from configuration
    username = config["username"]
    api_token = config["api_token"]
    base_url = config["base_url"]
    project_key = config["project_key"]
    feature_field_id = config["feature_field_id"]
    severity_field_id = config["severity_field_id"]
    max_results = config["max_results"]

    # Create headers with basic authentication
    headers = {"Content-Type": "application/json"}

    # Define JQL query to search for defects assigned to users part of the team
    jql_query = f'project = {project_key} AND cf[{feature_field_id}] is not EMPTY and status != CLOSED'

    # Define fields to include in the response
    fields = 'key'

    # Make the request to search for defects
    search_params = {
        'jql': jql_query,
        'fields': fields,
        'maxResults': max_results
    }
    search_url = f'{base_url}/search'
    search_response = make_request(search_url, (username, api_token), headers, search_params)

    if 'errorMessages' in search_response:
        print(f"Failed to retrieve defects. Status code: {search_response['status']}")
        print("Error response:", search_response)
        exit(1)

    issues = search_response['issues']

    with ThreadPoolExecutor() as executor:
        executor.map(process_issue, issues)

def create_pivot_file(file1, file2, file3):

    # Read features from file1 into a list
    with open(file1, 'r') as f:
        features_file1 = f.read().splitlines()

    # Create an empty list to store matching lines
    matching_lines = []

    # Loop through features in file1 and check if they exist in file2
    with open(file2, 'r') as f:
        for feature in features_file1:
            for line in f:
                if feature in line:
                    matching_lines.append(line)
            f.seek(0)  # Reset file pointer to the beginning for each feature

    # Write matching lines to file3
    with open(file3, 'w') as f:
        f.write(''.join(matching_lines))

    # Find features from file1 that didn't match and append their lines to file3
    with open(file3, 'a') as f:
        with open(file1, 'r') as features:
            for feature in features:
                if feature.strip() not in ''.join(matching_lines):
                    f.write(feature)

    print(f"Matching lines have been saved to {file3}.")



if __name__ == '__main__':

    with open(CONFIG_FILE) as f:
        global config
        config = json.load(f)

    output_file = config["output_file"]

    if os.path.exists(output_file):
        with open(output_file, "r+") as file:
            file.truncate(0)

    search_issues()

    feature_file = config["feature_file"]
    pivot_file = config["pivot_file"]

    create_pivot_file(feature_file, output_file, pivot_file)
