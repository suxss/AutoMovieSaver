import sqlite3

from models.config import Config
from models.filter import Filter
from models.movie_info import MovieInfo


class SQLiteFilter(Filter):
    def __init__(self, config: Config, logger):
        self.conn = sqlite3.connect('data/movies.db')
        self.logger = logger
        self.cursor = self.conn.cursor()

    def init_db(self):
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                year INTEGER NOT NULL,
                account_type TEXT NULL,
                account_id TEXT NULL 
            )
        ''')

    def record(self, movie: MovieInfo, account_type, account_id):
        self.cursor.execute(
            'insert into movies (name, year, account_type, account_id) values (?, ?, ?, ?)',
            [movie.title, movie.year, account_type, account_id]
        )

    def filter(self, movie: MovieInfo):
        self.cursor.execute('select * from movies where name = ? and year = ?', [movie.title, movie.year])
        values = self.cursor.fetchall()
        return len(values) > 0

    def close(self):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

