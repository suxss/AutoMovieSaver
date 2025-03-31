from abc import ABC, abstractmethod

from models.movie_info import MovieInfo


class Filter(ABC):
    @abstractmethod
    def filter(self, movie: MovieInfo) -> bool: ...

    @abstractmethod
    def record(self, movie: MovieInfo) -> None: ...

    @abstractmethod
    def close(self) -> None: ...
