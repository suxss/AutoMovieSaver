from dataclasses import dataclass


@dataclass
class MovieInfo:
    title: str
    year: int
    video_format: str
    edition: str