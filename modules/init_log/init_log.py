import sys, os
import json
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules'))
from config_module import config_module


class LogInitializer:
    
    def __init__(self, log_path, config_path, script_name, loglevel, utc_time=False):
        self.log_path = log_path
        self.config_path = config_path
        self.script_name = script_name
        self.loglevel = loglevel
        self.utc_time = utc_time

    def _object_to_json(self, string):
        return json.dumps(string, indent=4)

    def print_config_log(self):
        config_object = config_module.ConfigModule(self.config_path)
        config = config_object.read_config()
        with open(self.log_path, 'a') as log:
            log.write('The used config is:\n')
            log.write(self._object_to_json(config))
            log.write('\n')
            
    def print_init_log(self):
        if self.utc_time:
            date = datetime.now(timezone.utc)
        else:
            date = datetime.now()
        with open(self.log_path, 'a') as log:
            log.write('----------- INITIALIZING LOG '+self.script_name+' -----------\n')
            log.write('Initializing log at ' + date.strftime("%Y-%m-%dT%H:%M:%S%z") + '\n')
            log.write('The used log level is: ' + self.loglevel.upper() + '\n')
            
    def print_version_log(self, version_file):
        with open(version_file, 'r') as version_f:
            version = version_f.read()
            with open(self.log_path, 'a') as log:
                log.write('The version is: ' + version + '\n')
