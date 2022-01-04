import logging
import logging.handlers
import pathlib
import pickle
import socketserver
import struct
import re
import asyncio
import time

from queue import Queue

# LEVEL_LOGS
# CRITICAL = 50
# FATAL = CRITICAL
# ERROR = 40
# WARNING = 30
# WARN = WARNING
# INFO = 20
# DEBUG = 10
# NOTSET = 0

# Clase para configuar en los clonets/servidores


class MyLogger:
    """
    Clase configurador de logs
    Link: https://docs.python.org/3/library/logging.handlers.html
    """

    # TODO: hacer el tamaÃ±o del log como un parametro con nombre opcional "**kargs" -> https://realpython.com/python-kwargs-and-args/

    def __init__(self, alias, level, path, utc_time=False, propagate=False, log=None,
				filemode='maxsize', maxBytes=1048576, backupCount=10):
        self.alias = alias
        self.level = level
        self.path = path
        self.filemode = filemode
        self.utc_time = utc_time
        self.propagate = propagate
        self.maxBytes = maxBytes
        self.backupCount = backupCount
        self.log = log
        self.log = self.__crear(self.log)

    def __crear(self, log):
        """
        Metodo para configurar el configurador
        """
        log = logging.getLogger(self.alias)
        log.handlers.clear()
        log.setLevel(self.level)
        log.propagate = self.propagate

        return log

    def configurar_consola(self, log=None, level=None):
        """
        Metodo para configurar la salida por consola de cada log
        """
        if not log:
            log = self.log

        if not level:
            level = self.level

        handler_console = logging.StreamHandler()
        handler_console.setLevel(level)
        formatter = logging.Formatter(
            "'%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        formatter.datefmt = '%Y-%m-%dT%H:%M:%S%z'
        if self.utc_time:
            formatter.converter = time.gmtime
        handler_console.setFormatter(formatter)
        log.addHandler(handler_console)

    def configurar_fichero(self, log=None, path=None):
        """
        Metodo para configurar la ruta para registar los mensajes
        """
        if not log:
            log = self.log

        if not path:
            path = self.path

        #pathlib.Path(path).mkdir(parents=True, exist_ok=True)

        #file = path + self.alias + ".log"
        file = path
        if self.filemode == 'maxsize':
            handler_file = self.__configurar_size(file, self.maxBytes, self.backupCount)
        elif self.filemode == 'time':
            handler_file = self.__configurar_horario(file)
        else:
            handler_file = logging.FileHandler(
                file, "a+", encoding='utf-8', delay="true")

        handler_file.setLevel(self.level)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')
        formatter.datefmt = '%Y-%m-%dT%H:%M:%S%z'
        if self.utc_time:
            formatter.converter = time.gmtime
        handler_file.setFormatter(formatter)
        log.addHandler(handler_file)

    def __configurar_horario(self, file, horario='M'):
        """
        Metodo para configurar una rotacion del fichero del log en el tiempo
        """
        handler_time = logging.handlers.TimedRotatingFileHandler(
            file,
            encoding='utf-8',
            when=horario)

        return handler_time

    def configurar_queue_lister(self, log, queue=None):
        """
        Metodo para configurar una cola al log y devolver un listener para controlarla
        """
        if queue is None:
            queue = Queue(-1)
        if log is None:
            log = self.log

        queue_handler = logging.handlers.QueueHandler(queue)
        queue_listener = logging.handlers.QueueListener(queue, queue_handler)
        log.addHandler(queue_handler)
        return queue_listener

    def configurar_HTTP(self, log, host="localhost:8000", url='/'):
        """
        MÃ©todo para configurar el envio de logs a un equipo remoto a traves de HTTP
        """
        # handler_http = logging.handlers.HTTPHandler(
        #     host=host, url=url, method='POST', secure=false)

        handler_http = logging.handlers.HTTPHandler(
            host="localhost:8000", url="/lo", method="post")

        log.addHandler(handler_http)

    def __configurar_size(self, file, tamanyo=1048576, backupCount=10):
        handler_size = logging.handlers.RotatingFileHandler(
            file, encoding='utf-8', maxBytes=tamanyo, backupCount=backupCount)
        return handler_size

    def configurar_TCP(self, log, host="localhost", port=None, socket=None):
        """Metodo para configurar envios de log por TCP. Dos modos de funcionamiento:
            1. Si no se especifica un socket creado se crea una conexiÃ³n cliente con el host y puerto dado
            2. Si hay un socket creado se trabaja con Ã©l
        """
        if socket is None:
            log.warning("NO SE PUDO CREAR EL LOG POR TCP")
            return
        else:
            handler_tcp = logging.handlers.SocketHandler(host=None, port=None)
            handler_tcp.sock = socket
        log.addHandler(handler_tcp)

    def configurar_log_completo(self, log=None):
        "Metodo para configurar un log por completo"
        if not log:
            log = self.log

        self.configurar_consola(log)
        self.configurar_fichero(log, self.path)

        return log

    def getlog(self):
        "Funcion get para retonar el valor del log"
        return self.log

    def set_alias(self, alias):
        "Metodo set para cambiar el valor del nombre"
        self.alias = alias

    def set_level(self, level):
        "Metodo set para cambiar el valor del nivel de depuracion"
        self.level = level

    def set_path(self, path):
        "Metodo set para cambiar el valor del path"
        self.path = path


class ServidorLogTcp(asyncio.Protocol):
    def __init__(self, log, logger):
        self._logger = logger
        self._log = log

    def connection_made(self, transport):
        self.transport = transport

        self.socket_client = self.transport.get_extra_info('socket')

        self._connection = True
        peername = self.transport.get_extra_info('peername')
        self._log.info(
            'SERVER TCP: Conexion entrante desde {cliente}'.format(cliente=peername))
        self.start_sent_log(peername)

    def start_sent_log(self, peername):
        self._logger.configurar_TCP(
            self._log, peername[0], peername[1], self.socket_client)
        self._log.info("Test envio de registro")

    def stop_sent_log(self):
        for handler in self._log.handlers:
            if type(handler) == logging.handlers.SocketHandler:
                self._log.removeHandler(handler)
        self._log.info("Fin de envio de registros")

    def data_received(self, data):
        # message = data.decode()
        self._log.info(
            'SERVER: Datos en bruto recibidos {datos}'.format(datos=data))

    def connection_lost(self, exc):
        self._connection = False
        self.stop_sent_log()
        super().connection_lost(exc)


class Servicio_Log_TCP():

    def __init__(self, log, logger):
        self._logger = logger
        self._log = log
    """
    Servidor TCP para enviar registros de los logs
    """
    def stop(self):
        self._server.close()

    def run(self):
        self._loop = asyncio.get_event_loop()
        self.transport = asyncio.Transport()
        self._loop.create_task(self.servicio_log())
        self._server = None

    async def servicio_log(self):
        self._server = await self._loop.create_server(
            lambda: ServidorLogTcp(self._log, self._logger),
            '0.0.0.0', 9019)

        addr = self._server.sockets[0].getsockname()
        self._log.info('Servidor LOG-TCP funcionando {addr}'.format(addr=addr))
