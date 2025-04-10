from abc import ABC, abstractmethod

from models.movie_info import MovieInfo


class Filter(ABC):
    @abstractmethod
    def init_db(self) -> None: ...

    @abstractmethod
    def filter(self, movie: MovieInfo) -> bool: ...

    @abstractmethod
    def record(self, movie: MovieInfo, account_type, account_id) -> None: ...

    @abstractmethod
    def close(self) -> None: ...
