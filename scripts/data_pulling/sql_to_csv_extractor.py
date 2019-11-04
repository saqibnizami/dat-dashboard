import csv
import json
import logging
import os
import sys

import hvac
import psycopg2, pymysql

logging.basicConfig(filename=os.path.join(sys.path[0], 'sql_to_csv_extractor.log'), format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)


class VaultClient(object):
    def __init__(self, vault_host, vault_id, vault_token):
        self.vault_id = vault_id
        self.vault_token = vault_token
        self.client = hvac.Client(url=vault_host, token=vault_token)

    def get_secret(self, key):
        secrets = self.client.read('secret/production/' + self.vault_id + '/secrets/')['data']
        if not secrets or not secrets.get(key):
            raise Exception('Secret {} was not found on Vault'.format(key))
        return secrets.get(key)


class Utils(object):
    @staticmethod
    def read_file(file_name):
        with open(os.path.expanduser(file_name)) as f:
            return f.read()

    @staticmethod
    def get_absolute_path(relative_path):
        scriptdir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(scriptdir, relative_path)


vault_client = VaultClient('https://vault.ubiome.com:8200', 'ubiome-dat-dashboard', Utils.read_file('~/.vault/vault_token'))


class SqlToCsvExtractor:

    @staticmethod
    def main():
        config_file = sys.argv[1]

        with open(config_file) as f:
            configuration = json.load(f, strict=False)

            logging.info('Running with config {}'.format(config_file))


        is_update, query = SqlToCsvExtractor.resolve_query(configuration)

        logging.info('{} {}'.format('Updating' if is_update else 'Creating', configuration['output_file']))

        columns, records = SqlToCsvExtractor.fetch_data(
            vault_client.get_secret(configuration['vault_secret_with_db_credentials']),
            query)

        write_mode = 'a' if is_update else 'w'
        with open(Utils.get_absolute_path(configuration['output_file']), write_mode) as csvfile:
            writer = csv.writer(csvfile)
            if not is_update:
                writer.writerow(columns)
            writer.writerows(records)

        logging.info('Finished {} {} with {} rows'.format('updating' if is_update else 'creating', configuration['output_file'], len(records)))

    @staticmethod
    def fetch_data(db_credentials, query):
        try:

            if 'mysql' not in db_credentials['host']:
                connection = psycopg2.connect(user=db_credentials['user'],
                                              password=db_credentials['pw'],
                                              host=db_credentials['host'],
                                              port=db_credentials['port'],
                                              database=db_credentials['database'])
            else:
                connection = pymysql.connect(user=db_credentials['user'],
                                             password=db_credentials['pw'],
                                             host=db_credentials['host'],
                                             db=db_credentials['database'],
                                             charset='utf8mb4')

            cursor = connection.cursor()
            logging.info('Fetching data')
            cursor.execute(query)
            records = cursor.fetchall()
            columns = [i[0] for i in cursor.description]
            logging.info('Fetched {} rows'.format(len(records)))

            return columns, records
        except Exception as error:
            logging.error('Error while fetching data {}'.format(error))
            raise
        finally:
            if 'connection' in locals():
                cursor.close()
                connection.close()
                logging.info('Connection closed')


    @staticmethod
    def resolve_query(configuration):
        file_already_exists = os.path.isfile(Utils.get_absolute_path(configuration['output_file']))
        can_update_data = 'update_query_template' in configuration and 'update_query_param_source' in configuration

        if file_already_exists and can_update_data:

            with open(Utils.get_absolute_path(configuration['output_file'])) as csvfile:
                reader = csv.DictReader(csvfile)
                rows_list = list(reader)
                last_row = rows_list[len(rows_list)-1]
                update_query_param = last_row[configuration['update_query_param_source']]

            return True, configuration['update_query_template'].format(update_query_param)
        else:
            return False, configuration['query']


"""
Outputs the result of a query to a csv file.
Takes a configuration file with the following
schema as parameter:
    
{
    "output_file": "relative/path/target.csv",
    "vault_secret_with_db_credentials": "secrets_key",
    "db_name": "backend",
    "query": "SELECT * FROM orders.orders WHERE state NOT IN ('DRAFT') AND created_at > '2017-12-31' order by created_at asc",
    "update_query_template": "SELECT * FROM orders.orders WHERE state NOT IN ('DRAFT') AND created_at > {}'",
    "update_query_param_source": 'created_at'
}

When the output file already exists, 
the update_query_template is used if provided,
replacing the placeholder {} on it with the value
of the column specified in update_query_param_source
from the last row of the file.

If no update_query_template is provided, the output
file will be overwritten each time the script runs.

Usage:
$ python3 sql_to_csv_extractor.py /absolute/path/config_file.json
"""
if __name__ == '__main__':
    try:
        SqlToCsvExtractor.main()
    except Exception as e:
        logging.exception('Unhandled exception')
