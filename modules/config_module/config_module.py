'''
    This module implements functions that operate over config file
    
    This module ** IS THREAD-SAFE **
'''

import json, os, logging
from threading import RLock

class ConfigModule:

    def __init__(self, config_path, default_config_path=None):
        self.config_path = config_path
        self.default_config_path= default_config_path
        
        self.lock = RLock()
        
    def _object_to_json(self, string):
        return json.dumps(string, indent=4)
    
    def _json_to_object(self, string):
        return json.loads(string)
        
    def _write_in_config(self, content):
        self.lock.acquire()
        logging.info('Writing config: [' + str(content) + '] to config file.')
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=4)
        logging.info('Config written succsessfully')
        self.lock.release()
    
    def _ls(self,path='./'):
        files = os.listdir(path)
        files = [path + f for f in files]
        return files
    
    
    
    ##############----Functions to export--------############
    
    '''
    Read config_file.json.
    
    Return JSONObject if path exists and file can be readed.
    '''
    def read_config(self):
        self.lock.acquire()
        logging.info('Reading config file')
        try:
            with open(self.config_path) as f:
                content = f.read()
        except Exception as e:
            logging.error('Error reading config file: ' + str(e))
            return
        logging.info('Config file read succsessfully')
        self.lock.release()
        return self._json_to_object(content)

    '''
    Add a new variable to config file.
    If variable already exists, it`s replace by the new value
    
    Return True if all go good. False otherwise
    '''
    def add_variable_config(self, key, value):
        self.lock.acquire()
        logging.info('Adding value: ' + str(key) + ':' + str(value) + ' to config')
        try:
            config = self.read_config()
            config[key] = value
            self._write_in_config(config)
            logging.info('Value ' + str(key) + ':' + str(value) + ' added to config succsessfully.')
            self.lock.release()
            return True
        except Exception as e:
            logging.error('Can not add value: ' + str(key) + ':' + str(value) + ' to config: ' + str(e))
            self.lock.release()
            return False
            
    '''
    Remove a variable from config file.
    
    Return False if variable doesn't exists. True otherwise
    '''
    def rm_variable_config(self, variable):
        self.lock.acquire()
        logging.info('Removing variable: ' + str(variable) + ' from config')
        try:
            config = self.read_config()
            del config[variable]
            self._write_in_config(config)
            logging.info('Variable: ' + str(variable) + ' removed from config succsessfully.')
            self.lock.release()
            return True
        except Exception as e:
            logging.error('Can not remove variable: ' + str(variable) + ' from config: ' + str(e))
            self.lock.release()
            return False
    
    
    '''
    Restore default configuration.
    
    Return True if can set default conf. False otherwise
    '''
    def set_default_config(self):
        self.lock.acquire()
        logging.info('Setting default config')
        try:
            with open(self.default_config_path) as f:
                content = f.read()
                default_config = self._json_to_object(content)
                self._write_in_config(default_config)
            logging.info('Set default config succsessfully')
            self.lock.release()
            return True
        except Exception as e:
            logging.error('Can not set default config: ' + str(e))
            self.lock.release()
            return False

