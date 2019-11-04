from app import config

def relpath(path):
    """
    Prefix relative URLs with the Dash app name in case that
    the app is deployed on dev environments.
    """
    if config.get('base_path'):
        return '/{}{}'.format(config.get('base_path'), path)
    return path
