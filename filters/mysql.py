import mysql.connector

from models.config import Config
from models.filter import Filter
from models.movie_info import MovieInfo


class MySQLFilter(Filter):
    def __init__(self, config: Config, logger):
        self.config = config
        self.logger = logger
        self.conn = mysql.connector.connect(user=config.db_info.username, password=config.db_info.password, database=config.db_info.database)
        self.cursor = self.conn.cursor()

    def init_db(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name TEXT NOT NULL,
                year INTEGER NOT NULL,
                account_type TEXT NULL,
                account_id TEXT NULL 
            )
        ''')
        self.conn.commit()

    def filter(self, movie: MovieInfo) -> bool:
        self.cursor.execute('select * from movies where name = %s and year = %s', [movie.title, movie.year])
        values = self.cursor.fetchall()
        return len(values) > 0

    def record(self, movie: MovieInfo, account_type, account_id) -> None:
        self.cursor.execute('insert into movies (name, year) values (%s, %s)', [movie.title, movie.year])

    def close(self):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

