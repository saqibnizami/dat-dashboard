import json
import logging
import os
import sys
import time

import hvac
import pandas
import requests

logging.basicConfig(filename=os.path.join(sys.path[0], 'metabase_to_csv_extractor.log'), format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)


class Utils(object):
    @staticmethod
    def read_file(file_name):
        with open(os.path.expanduser(file_name)) as f:
            return f.read()

    @staticmethod
    def get_absolute_path(relative_path):
        scriptdir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(scriptdir, relative_path)


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


vault_client = VaultClient('https://vault.ubiome.com:8200', 'ubiome-dat-dashboard', Utils.read_file('~/.vault/vault_token'))


class MetabaseClient(object):

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.auth_token = self.login()['id']

    def login(self):
        login_response = requests.post(
            'https://metabase.ubiome.io/api/session',
            data=json.dumps({'username': self.username, 'password': self.password}),
            headers={'Content-Type': 'application/json'}
        ).json()

        return login_response

    def get_question(self, question_id):
        t1 = time.time()
        response = requests.post(
            'https://metabase.ubiome.io/api/card/{}/query/json'.format(question_id),
            headers={'Content-Type': 'application/json', 'X-Metabase-Session': self.auth_token}
        )

        logging.info('Metabase request took {}s seconds'.format(time.time()-t1))
        if response.ok:
            return response
        raise Exception('Question {} could not be fetched. Response code: {}. Reason:'.format(question_id, response.status_code, response.reason))


metabase_credentials = vault_client.get_secret('metabase')
metabase_client = MetabaseClient(metabase_credentials['user'], metabase_credentials['pass'])


class MetabaseToCsvExtractor:

    @staticmethod
    def main():
        config_file = sys.argv[1]

        with open(config_file) as f:
            configuration = json.load(f, strict=False)

            logging.info('Running with config {}'.format(config_file))

        logging.info('Creating {}'.format(configuration['output_file']))
        response = metabase_client.get_question(configuration['question_id'])

        response_df = pandas.DataFrame(response.json())

        path = os.path.dirname(Utils.get_absolute_path(configuration['output_file']))
        os.makedirs(path, exist_ok=True)
        response_df.to_csv(Utils.get_absolute_path(configuration['output_file']))

        logging.info('Finished creating {}'.format(configuration['output_file']))


"""
Outputs the result of a metabase question to a csv file.
Takes a configuration file with the following
schema as parameter:
    
{
    "output_file": "relative/path/target.csv",
    "question_id": "123"
}

The output file will be overwritten on each run.

Usage:
$ python3 metabase_to_csv_extractor.py /absolute/path/config_file.json
"""
if __name__ == '__main__':
    try:
        MetabaseToCsvExtractor.main()
    except Exception as e:
        logging.exception('Unhandled exception')
