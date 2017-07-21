# coding: utf-8

from __future__ import print_function, unicode_literals

import bottle
import configparser
import webbrowser

from boxsdk import Client, OAuth2
from threading import Thread, Event
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server

REQUEST_COUNT = 100


def _create_items(item, parent, file_list):
    if item.type == 'file':
        box_file = BoxObject(item.id, item.name, parent)
        file_list.append(box_file)
    if item.type == 'folder':
        box_folder = BoxObject(item.id, item.name, parent)
        for sub_item in _retrieve_all_items(item):
            _create_items(sub_item, box_folder, file_list)


def _retrieve_all_items(parent_folder):
    offset = 0
    all_items = None
    while True:
        new_items = parent_folder.get_items(limit=REQUEST_COUNT, offset=offset)
        if all_items is None:
            all_items = new_items
        else:
            all_items = all_items + new_items
        if len(new_items) < REQUEST_COUNT:
            return all_items
        offset += REQUEST_COUNT


class Box(object):
    def __init__(self, path_prefix, root_directory=None, oauth_class=OAuth2, reset_cred=True, build=True):
        self.name = 'Destination'
        self.client = None
        self.files = None
        self._owner = None
        self.path_prefix = path_prefix

        self._authenticate(reset_cred, oauth_class)
        if build:
            self._build_box(root_directory)

    @property
    def owner(self):
        return ''

    def _authenticate(self, force_refresh, oauth_class=OAuth2):
        class StoppableWSGIServer(bottle.ServerAdapter):
            def __init__(self, *args, **kwargs):
                super(StoppableWSGIServer, self).__init__(*args, **kwargs)
                self._server = None

            def run(self, app):
                server_cls = self.options.get('server_class', WSGIServer)
                handler_cls = self.options.get('handler_class', WSGIRequestHandler)
                self._server = make_server(self.host, self.port, app, server_cls, handler_cls)
                self._server.serve_forever()

            def stop(self):
                self._server.shutdown()

        # Config setup
        cfg = configparser.ConfigParser()
        cfg.read('fivium_temp.cfg')
        client_id = cfg['client_info']['client_id']
        client_secret = cfg['client_info']['client_secret']

        # Verify if there is a valid token already
        if 'app_info' in cfg and not force_refresh:
            access_token = cfg.get('app_info', 'access_token')
            refresh_token = cfg.get('app_info', 'refresh_token')

            self.client = Client(oauth_class(
                client_id=client_id,
                client_secret=client_secret,
                access_token=access_token,
                refresh_token=refresh_token))
        else:
            auth_code = {}
            auth_code_is_available = Event()

            local_oauth_redirect = bottle.Bottle()

            @local_oauth_redirect.get('/')
            def get_token():
                auth_code['auth_code'] = bottle.request.query.code
                auth_code['state'] = bottle.request.query.state
                auth_code_is_available.set()

            local_server = StoppableWSGIServer(host='localhost', port=8080)
            server_thread = Thread(target=lambda: local_oauth_redirect.run(server=local_server))
            server_thread.start()

            oauth = oauth_class(
                client_id=client_id,
                client_secret=client_secret,
            )
            auth_url, csrf_token = oauth.get_authorization_url('http://localhost:8080')
            webbrowser.open(auth_url)

            auth_code_is_available.wait()
            local_server.stop()
            assert auth_code['state'] == csrf_token
            access_token, refresh_token = oauth.authenticate(auth_code['auth_code'])

            if 'app_info' not in cfg:
                cfg['app_info'] = {}

            cfg['app_info']['access_token'] = access_token
            cfg['app_info']['refresh_token'] = refresh_token
            with open('app.cfg', 'w') as configfile:
                cfg.write(configfile)

            self.client = Client(oauth)

    def _build_box(self, root_directory):
        root_item = self._get_root(root_directory)
        box_items = _retrieve_all_items(self.client.folder(folder_id=root_item.id))
        self.files = []
        for item in box_items:
            _create_items(item, root_item, self.files)

    def _get_root(self, root_directory):
        if root_directory is None:
            return BoxObject('0', self.path_prefix, None)
        paths = root_directory.split('/')
        current_folder_id = '0'
        for path_item in paths:
            box_items = _retrieve_all_items(self.client.folder(folder_id=current_folder_id))
            found_path = False
            for box_item in box_items:
                if box_item.type == 'folder' and box_item.name == path_item:
                    found_path = True
                    current_folder_id = box_item.id
                    break
            if not found_path:
                raise FileNotFoundError('Couldn\'t find the root folder <{0}> in box'.format(root_directory))
        return BoxObject(current_folder_id, self.path_prefix, None)

    def apply_metadata(self, drive, base_folder_path=''):
        base_folder_path = self.path_prefix + base_folder_path
        for box_file in self.files:
            if base_folder_path in box_file.name:
                drive_file = drive.get_file_via_path(box_file.path, None)
                if drive_file:
                    metadata = self.client.file(box_file.id).metadata('enterprise', 'legacyData')
                    if metadata.get() is None:
                        metadata.create({'owner': drive_file.owner.name,
                                         'legacyCreatedDate': drive_file.created_time,
                                         'legacyLastModifyingUser': drive_file.last_modified_by.name,
                                         'legacyLastModifiedDate': drive_file.last_modified_time})
                        print('matched file: ' + box_file.path)
                    else:
                        print('The legacy metadata already exists for ' + box_file.path + ', skipping')


class BoxObject(object):
    """ File representation class

    Args:
        identifier (str): Google Drive ID of the file
        name (str): Name of the file
        parent ([str]): List of parent IDs

    Attributes:
        id (str): Google Drive ID of the file
        name (str): Name of the file
        parent ([str]): List of parent IDs
        path (str): Path to the file within the Drive

    """

    def __init__(self,
                 identifier,
                 name,
                 parent):
        self.id = identifier
        self.name = name
        self.parent = parent

        if self.parent is not None:
            self.path = self.parent.path + '/' + self.name
        else:
            self.path = name

    def __repr__(self):
        return "<file: {0}>".format(self.name)
