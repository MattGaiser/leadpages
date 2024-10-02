# Leadpages ETL Demonstration

A project is never perfect, particularly when one is building for an ambiguous future (such as an interview driven animal focused startup). To keep this exercise within a reasonable amount of time, the following shall be out of scope:

- Cleaning up the auto generated boilerplate in `settings.py`. Yes, a lot is not needed, but it would take a fair bit of time to entirely remove.
- General Django new project best practices, such as overriding the default user model, making separate apps for every bit of functionality, setting models to UUIDs by default, or versioning the API.
- Authentication and security in general. The test API has none and this API will not be secured by one. Celery will just run on root. .env will not be configured for the secret. Debug will default to true.
- Substantial logging and general error handling beyond the problems specified in the task.
- Perfectly hostable project version. The URL is hardcoded to localhost rather than dealing with environment variables.

## A Brief Architectural Discussion

### Why Django?
I chose Django because it is a highly suitable base for a startup product. It allows you to move quickly as many of the key decisions are made by default, has a robust community, and lets you build interfaces between the web and tasks easily.

### Why Celery?
ETL tasks take a long time to run, so better to not have it block the main process and best to parallelize it as much as possible.

### Why VCR? 
VCR is a wonderful library that allows the tests to use the actual API calls rather than mocks. This has two major benefits. First, it doesn't take long to make the cassettes as they are just recordings. Second, they are the actual API calls and in a real integration, they contain the same authentication mechanisms, header details, and errors that may be found in real API calls, but are often ignored in mocks.  

### The Merits of this Approach
What easy to use and maintain means differs greatly between people. To me, easy to use and maintain has a few requirements:

1. It runs reasonably quickly, allowing debugging in much shorter periods of time. That’s why there are multiple tasks and multiple threads. This is especially important with the unreliable base API, which is known to regularly lag or have errors as per the assignment.
2. It uses technology I know. Django and Celery are technologies I am experienced with. Depending on the specifics, this may not be an ideal approach, but given the ambiguity of the assignment, it does the job and can serve as the base of an animal startup. 
3. It has logging to allow errors to be quickly identified. One of the most vexing challenges I have had with ETL is unclear logging, with vague “task failed” messages being the starting point for investigating how a pipeline failed. 
4. I can easily access reports and share reports with others as well as trigger the task from a dashboard (or perhaps via an API, such as when I worked at OneTrust). 
5. It is extensible. The pattern used here matches the integrations I built at OneTrust that had custom client base endpoints. 


### Alternatives Ruled Out

#### Cron job
The instructions say this should be the foundation of an animal based startup. I am biased, but where I worked previously, the data was part of a broader evidence collecting web app and merely putting it into a database with a cron job is less integrated than triggering it via a web app. Celery is a kind of cron job for Python web apps anyway. 

#### Script 
Explicitly excluded as per the instructions. 

#### Lambda/Cloud Function
Depending on how large the dataset is, this one is actually a popular option as quite a bit can fit within the free tier. I skipped this one as it wouldn't demonstrate much technical skill, but it would be a suitable answer for the scale of this task. It does get quite expensive at scale though. 