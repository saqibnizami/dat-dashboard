import os
import hvac
from hvac.exceptions import Forbidden

VAULT_URL='https://vault.ubiome.com:8200'

def file_home_token(file_name):
   with open(os.path.expanduser(file_name)) as f:
       return f.read().rstrip('\n')


def file_home_token(file_name):
    with open(os.path.expanduser(file_name)) as f:
        return f.read().rstrip('\n')

def load(app_name):
    VAULT_ID = os.environ.get('UBIOME_ENVIRONMENT')
    if VAULT_ID == 'development':
        # if using personal env, uncomment the following line, else 'dev' secrets will be used
        VAULT_ID = file_home_token('~/.vault/vault_id')
        os.environ.setdefault('VAULT_TOKEN', file_home_token('~/.vault/vault_token'))
    elif VAULT_ID == 'docker':
        VAULT_ID = file_home_token('/home/{}/.vault/vault_id'.format(app_name))
    elif VAULT_ID != 'ci':
        os.environ.setdefault('VAULT_TOKEN', file_home_token('/home/{}/.vault/vault_token'.format(app_name)))

    client = hvac.Client(url=VAULT_URL, token=os.environ.get('VAULT_TOKEN'))
    secrets_path = 'secret/{}/{}/secrets'.format(VAULT_ID, app_name)
    try:
        response = client.read(secrets_path)
        if response is None:
            raise Exception("No secrets data found for path: {}".format(secrets_path))
        return response['data']
    except Exception as e:
        if isinstance(e, Forbidden):
            raise Exception("You don't have access or secrets don't exist in path {}".format(secrets_path))
        raise e