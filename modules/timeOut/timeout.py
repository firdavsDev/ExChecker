from time import monotonic, process_time
from typing import Callable
import sys


class TimeOut:
    def __init__(self, milliseconds: int = 0, seconds: int = 0, minutes: int = 0, hours: int = 0, start: bool = True) -> None:
        """Constructor de la clase, establece el tiempo del timeout e inicia en el momento de la construcción si se define a traves de su parametro start.
        En caso de no iniciar en la construcción del objeto, se puede iniciar en con el metodo start.
        Args:
            milliseconds (int, optional): valor que representa a milisegundos. Defaults to 0.
            seconds (int, optional): valor que representa a segundos. Defaults to 0.
            minutes (int, optional): valor que representa a minutos. Defaults to 0.
            hours (int, optional): valor que representa a horas Defaults to 0.
            start (bool, optional): valor booleano que define si el timeout inicia en el momento de la construcción o no se inicia. Defaults to True.
        """
        self.function_time = monotonic
        gettrace = getattr(sys, 'gettrace', None)
        if gettrace():
            self.function_time = process_time
            print('iniciando timeout en modo depuración')
        self.set_time(milliseconds=milliseconds, seconds=seconds,
                      minutes=minutes, hours=hours)
        self._start = start

    @property
    def is_expired(self) -> bool:
        """Propiedad que retorna el estado del timeout.

        Returns:
            bool: Si el tiemout se completo retorna True, en caso contrario retorna False.
        """
        return (self.function_time() > self._max) if self._start else (self._pause > self._max)

    @property
    def is_expired_and_not_stoped(self) -> bool:
        """Propiedad que retorna:
            True si el timer ha expirado y esta corriendo.
            False si el timer no ha expirado o esta parado

        Returns:
            bool: Si el tiemout se completo retorna True, en caso contrario retorna False.
        """
        return (self.function_time() > self._max) if self._start else False

    @property
    def is_started(self) -> bool:
        """Propiedad que retorna un booleano que dice si el timeout esta activo o no.

        Returns:
            bool: Si el tiemout esta contando retorna True en caso contrario retorna False.
        """
        return self._start

    @property
    def elapsed(self) -> float:
        """Propiedad que retorna el tiempo transcurrido desde que se inicio el timeout.

        Returns:
            float: Tiempo transcurrido en francción de segundos.
        """
        elapsed = (self.function_time() -
                   self._init) if self._start else (self._pause - self._init)
        return elapsed if elapsed < self._max else self._time

    @property
    def remaining(self) -> float:
        """Propiedad que retorna el tiempo restante hasta que timeout se cumpla.

        Returns:
            float: Tiempo restante en fracción de segundos.
        """
        remaining = self._time - self.elapsed
        return remaining if remaining > 0.0 else 0.0

    def set_time(self, milliseconds: int = 0, seconds: int = 0, minutes: int = 0, hours: int = 0) -> None:
        """Metodo que establece el timer del timeout.

        Args:
            milliseconds (int, optional): valor que representa a milisegundos. Defaults to 0.
            seconds (int, optional): valor que representa a segundos. Defaults to 0.
            minutes (int, optional): valor que representa a minutos. Defaults to 0.
            hours (int, optional): valor que representa a horas Defaults to 0.

        Raises:
            TypeError: Si el valor pasado no es de tipo int se levanta un typeError.
        """
        for attribute in [milliseconds, seconds, minutes, hours]:
            if not isinstance(attribute, int):
                raise TypeError(f'{type(attribute)} not valid')
        self._time = (milliseconds/1000) + seconds + \
            (minutes * 60) + (hours * 3600)
        self.reset()

    def get_time(self):
        return self._time

    def start(self, function: Callable[[], bool] = lambda: True) -> None:
        """Metodo que inicia o reanuda el timeout si el tiemout esté esta parado, en caso contrario no hace nada.
        Args:
            function (Callable[[], bool], optional): Función opcional, si retorna True el timeout se inicia o reanuda en caso contrario no se inicia o reanuda.
            Defaults to lambda:True.
        """
        if function() and not self._start:
            diference = self.function_time() - self._pause
            self._init += diference
            self._max += diference
            self._start = True
            self._pause = self._init

    def stop(self, function: Callable[[], bool] = lambda: True) -> None:
        """Metodo que para el timeout si el tiemout esta iniciado, en caso contrario no hace nada.
        Args:
            function (Callable[[], bool], optional): Función opcional, si retorna True el timeout se detiene en caso contrario no se detiene. Defaults to lambda:True.
        """
        if function() and self._start:
            self._start = False
            self._pause = self.function_time()

    def reset(self, function: Callable[[], bool] = lambda: True, run: bool = None) -> None:
        """Método que resetea el tiemout.
        Args:
            function (Callable[[], bool], optional): Función opcional, si retorna True el timeout se resetea en caso contrario no se resetea. Defaults to lambda:True.
            run: bool=None si se quiere que arranque o pare cuando se resete el timer
        """
        if function():
            self._init = self.function_time()
            self._pause = self._init
            self._max = self._init + self._time

        if run:
            self._start = True
        elif run is False:
            self._start = False
