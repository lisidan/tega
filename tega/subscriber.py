import tega.idb
import tega.tree

from abc import ABCMeta, abstractmethod
from enum import Enum
import importlib
import imp
import inspect
import os
import sys

class SCOPE(Enum):
    '''
    Subscription scope.
    '''
    LOCAL = 'local'    # SUB to local idb (not to global idb)
    GLOBAL = 'global'  # SUB from a plugin to global idb via local idb 

class Subscriber(object):

    def __init__(self, tega_id, scope=SCOPE.LOCAL):
        self._tega_id = tega_id
        self._scope = scope

    @property
    def tega_id(self):
        '''
        tega ID of this plugin.
        '''
        return self._tega_id

    @tega_id.setter
    def tega_id(self, value):
        self._tega_id = value

    @property
    def scope(self):
        '''
        Scope of this subscriber. 
        '''
        return self._scope

    @abstractmethod
    def on_init(self):
        '''
        Driver initialization completed.
        '''
        pass

    @abstractmethod
    def on_notify(self, notifications):
        '''
        Notifications in the form of [{},...].
        '''
        pass

    @abstractmethod
    def on_message(self, channel, tega_id, message):
        '''
        Message in the form of {}.
        '''
        pass

    '''
    TODO: forwarders implement this:
    def on_subscribe(self, path):
        pass
    '''

class PlugIn(Subscriber):

    def __init__(self, tega_id=None, scope=SCOPE.LOCAL):
        if tega_id:
            self._tega_id = tega_id
        else:
            self._tega_id = self.__class__.__name__
        self._scope = scope
        self.subscribe(self.tega_id, SCOPE.GLOBAL)
        tega.idb.add_tega_id(self.tega_id)

    @abstractmethod
    def initialize(self):
        '''
        The method is called by server.py to initialize this plugin.
        '''
        pass

    @abstractmethod
    def on_notify(self, notifications):
        '''
        Notifications in the form of [{},...].
        '''
        pass

    @abstractmethod
    def on_message(self, channel, tega_id, message):
        '''
        Message in the form of {}.
        '''
        pass

    def tx(self):
        '''
        Calls tega.idb.tx().
        '''
        return tega.idb.tx(subscriber=self)

    def func(self, method, *args, **kwargs):
        '''
        Creates tega.tree.Func() object and returns it.
        '''
        return tega.tree.Func(self.tega_id, method, *args, **kwargs)

    def rpc(self, path, *args, **kwargs):
        '''
        Calls tega.idb.rpc2().
        '''
        return tega.idb.rpc2(path, args, kwargs, self.tega_id)

    def subscribe(self, path, scope=None, regex_flag=False):
        '''
        Calls tega.idb.subscribe().
        '''
        if scope == None:
            scope = self.scope 
        tega.idb.subscribe(self, path, scope, regex_flag)

    def unsubscribe(self, path, regex_flag=False):
        '''
        Calls tega.idb.unsubscribe().
        '''
        tega.idb.unsubscribe(self, path, regex_flag)

    def get(self, path, version=None, regex_flag=False):
        '''
        Calls tega.idb.get().
        '''
        return tega.idb.get(path, version, regex_flag)

def plugins(plugin_paths):
    '''
    Returns a list of PlugIn subclasses.

    TODO: use find_spec() instead.
    '''
    PACKAGE = 'plugins'
    classes = []
    for plugin_path in plugin_paths:
        sys.path.append(plugin_path)
        for script in os.listdir(os.path.join(plugin_path, PACKAGE)):
            if script.endswith('.py'):
                mod_name = script.replace('.py', '')
                mod_str = '{}.{}'.format(PACKAGE, mod_name)
                try:
                    if mod_str in sys.modules:
                        mod = imp.reload(sys.modules[mod_str])
                    else:
                        mod = importlib.import_module('{}.{}'.format(PACKAGE, mod_name))
                    for name, class_ in inspect.getmembers(mod, inspect.isclass):
                        if issubclass(class_, PlugIn):
                            classes.append(class_)
                except ImportError:
                    raise
    return classes

