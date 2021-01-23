from graphql.validation import rules
import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

debug = True if os.environ.get('DEBUG') == 'True' else False


def get_empty_suggested_field_names(schema, graphql_type, field_name):
    return []


def get_empty_suggested_type_names(schema, output_type, field_name):
    return []


if debug is True:
    rules.fields_on_correct_type.get_suggested_field_names = get_empty_suggested_field_names
    rules.fields_on_correct_type.get_suggested_type_names = get_empty_suggested_type_names