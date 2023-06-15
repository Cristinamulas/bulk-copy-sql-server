# -*- coding: utf-8 -*-

# Import the helpers for custom recipes
from dataiku.customrecipe import get_input_names_for_role
from dataiku.customrecipe import get_output_names_for_role
from dataiku.customrecipe import get_recipe_config
import dataiku
import pandas as pd, numpy as np
import bcpy
import os
import pyodbc
import re
#adding

# To  retrieve the folder of an input role 
input_folder_name = get_input_names_for_role('folder_name')[0]
input_folder = dataiku.Folder(input_folder_name) # create a folder object


# user parameters
name_file = get_recipe_config()['file_name'] # file name test_5.csv
connection = get_recipe_config()['sql_connection'] # sql connection gcp-ms-sql
dataset_file = get_recipe_config()['file_dataset'] # name of the dataset

# get the file path
input_folder_path = dataiku.Folder(input_folder_name).get_path()
path_of_csv = os.path.join(input_folder_path, name_file)

# get the schema of the table
client = dataiku.api_client()
project = client.get_project(dataiku.default_project_key())
dataset_input = project.create_upload_dataset(dataset_file)# you can add connection= for the target connection
with open(path_of_csv, "rb") as f:
        dataset_input.uploaded_add_file(f, name_file)
# We run autodetection
settings = dataset_input.autodetect_settings()
settings.save()

        
input_dataset_schema = dataset_input.get_schema()
list_of_columns_names_input = [i['name'] for i in input_dataset_schema['columns']]

# encripting the password using secrets
auth_info = client.get_auth_info(with_secrets=True)
connection = client.get_connection(connection)
connection_definition = connection.get_definition()
sql_config =  {
    'server': connection_definition['params']['host'],
    'database': connection_definition['params']['db'],
    'username': connection_definition['params']['user'],
    'password': auth_info['secrets'][0]['value']
}


# For outputs, the process is the same:
output_A_names = get_output_names_for_role('database_output')[0]
output_A_names_fine = output_A_names.replace(".", "_")
sql_table_name = output_A_names_fine
csv_file_path = path_of_csv
flat_file = bcpy.FlatFile(qualifier='',columns = list_of_columns_names_input, path=csv_file_path)
sql_table = bcpy.SqlTable(sql_config, table=sql_table_name)
flat_file.to_sql(sql_table)
getting_name_dataset = re.findall(r'\.\s*(\w+)', output_A_names)[0]

dataset_out = project.get_dataset(getting_name_dataset)
dataset_out.set_schema(input_dataset_schema)
