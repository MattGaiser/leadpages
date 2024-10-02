# Leadpages ETL Demonstration

A project is never perfect, particularly when one is building for an ambiguous future (such as an interview driven animal focused startup). To keep this exercise within a reasonable amount of time, the following shall be out of scope:

- Cleaning up the auto generated boilerplate in `settings.py`. Yes, a lot is not needed, but it would take a fair bit of time to entirely remove.
- General Django new project best practices, such as overriding the default user model, making separate apps for every bit of functionality, setting models to UUIDs by default, or versioning the API.
- Authentication and security in general. The test API has none and this API will not be secured by one. Celery will just run on root. .env will not be configured for the secret. Debug will default to true.
- Substantial logging and general error handling beyond the problems specified in the task.
- Perfectly hostable project version. The URL is hardcoded to localhost rather than dealing with environment variables.

## A Brief Architectural Discussion

### Why Django?

### Why Celery?

