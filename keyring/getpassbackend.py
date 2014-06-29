"""Specific support for getpass."""
import getpass

from keyring import core


def get_password(prompt='Password: ', stream=None,
                 service_name='Python',
                 username=None):
    if username is None:
        username = getpass.getuser()
    return core.get_password(service_name, username)
