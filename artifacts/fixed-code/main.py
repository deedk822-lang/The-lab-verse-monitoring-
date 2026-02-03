from sqlalchemy import create_engine, text

# Replace 'your_db_url' with your actual database URL
DATABASE_URL = "your_db_url"

engine = create_engine(DATABASE_URL)

class AutoGLM:
    def __init__(self, db_connection):
        self.connection = db_connection

    async def query_database(self, query: str, parameters=None):
        if parameters is None:
            parameters = {}

        with self.connection.connect() as conn:
            result = await conn.execute(text(query), parameters)
            return result.fetchall()