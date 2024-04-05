import pip._vendor.requests as requests
import sys
import json
import os
import config

#-------------INITIALISE ENVIRONMENT-----------------#
# Set request headers and API token values
start_domain = config.start_domain
start_sub_url = config.start_sub_url
start_apitoken = config.start_apitoken  # insert api token value
start_head = config.start_head

element_size = '?size=10000'
sys.stdout.reconfigure(encoding='utf-8')

# Update for handling of XML
export_head = start_head.copy()
export_head['Accept'] = 'application/xml'

#-------------GET ALL libraries domain 1-----------------------#
# Update URL
start_sub_url = '/api/v2/libraries' + element_size
start_url = start_domain + start_sub_url

# GET request
response = requests.get(start_url, headers=start_head)

print("\n DOMAIN 1 \n")
# If successful
if response.status_code == 200:
    print("Get request successful")
    response1 = response.json()

# Initialize an empty list to store dictionaries for each library
libraries_info = []

# Filter response
items = response1.get('_embedded', {}).get('items', [])

#for every item in the response, store some library data
for item in items:
    if item.get('type').lower() == 'custom':  # If a custom library
        # Create a dictionary for each library
        library_dict = {
            'id': item.get('id'),
            'name': item.get('name'),
            'referenceId': item.get('referenceId'),
            'filePath': None  # Initialised as empty -> will populate following library export
        }
        # Append the dictionary to the list
        libraries_info.append(library_dict)

# Create folder to store XML files
if not os.path.exists('exports'):
    os.makedirs('exports')


# Get the library details and store XML
for library in libraries_info:
    print(library['id'], library['name'], library['referenceId'])
    
    # Update URL for library export
    start_sub_url = '/api/v2/libraries/' + str(library['id']) + '/export'
    start_url = start_domain + start_sub_url

    # GET request with updated headers to accept XML
    response = requests.get(start_url, headers=export_head)
    print("Export URL:", start_url)
    print("Status code:", response.status_code)

    # Save the export if successful
    if response.status_code == 200:
        # Define the path dynamically based on the library ID
        file_path = os.path.join('exports', f"{library['id']}.xml")
        with open(file_path, 'wb') as file:
            file.write(response.content)
        
        # Update the filePath in the library's dictionary
        library['filePath'] = file_path

        print(f"Successfully saved: {file_path}")
    else:
        print(f"Failed to export library {library['id']}. Status code: {response.status_code}")

# Print out the updated library information including the file paths
#you can comment this out for nicer output. This is mostly used for testing purposes.
print("\nUpdated Library Information:")
for library in libraries_info:
    print(f"ID: {library['id']}, Name: {library['name']}, Reference ID: {library['referenceId']}, File Path: {library.get('filePath', 'Not saved')}")


#SECOND ENVIRONMENT
post_domain = config.post_domain
post_sub_url = config.post_sub_url
post_apitoken = config.post_apitoken
post_head = config.post_head

post_sub_url = '/api/v2/libraries/import'
post_url = post_domain + post_sub_url

for library in libraries_info:
    # Ensure the file path exists and is not None before attempting to POST
    if library.get('filePath') and os.path.exists(library['filePath']):
        with open(library['filePath'], 'rb') as file:
            # Construct the files dictionary for multipart encoding
            files = {
              #file to be passed for import (export file from first environment)
                'file': (os.path.basename(library['filePath']), file),
            }
            # Data to be sent along with the file in the form data
            data = {
                "referenceId": library['referenceId'],
                "name": library['name']
            }
            
            response = requests.post(post_url, headers=post_head, data=data, files=files)
            #print(response) #commented out. feel free to uncomment this for testing purposes.
            if response.status_code == 200:
                print(f"Successfully imported {library['name']}.")
            else:
                # Including response.text to provide more details on why the request might have failed
                print(f"Failed to import {library['name']}. Status code: {response.status_code} - {response.text}")
    else:
        print(f"File path for {library['name']} not found or does not exist.")
