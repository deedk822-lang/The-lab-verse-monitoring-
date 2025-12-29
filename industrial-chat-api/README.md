# Industrial Grade Chat API

This is a Spring Boot application that provides an industrial-grade chat API using Spring AI, Spring Integration, and a PGVector database.

## Configuration

The application requires a PostgreSQL database with the PGVector extension. You can configure the database connection using the following environment variables:

- `DB_URL`: The JDBC URL of the database. Defaults to `jdbc:postgresql://localhost:5432/industrial_vault`.
- `DB_USERNAME`: The username for the database. Defaults to `postgres`.
- `DB_PASSWORD`: The password for the database. Defaults to `password`.

You will also need to provide an OpenAI API key for the chat client:

- `SPRING_AI_OPENAI_API_KEY`: Your OpenAI API key.

## Running the Application

You can run the application using the following Maven command:

```bash
mvn spring-boot:run
```
