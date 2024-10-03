# Leadpages ETL Demonstration

A project is never perfect, particularly when one is building for an ambiguous future (such as an interview driven animal focused startup). To keep this exercise within a reasonable amount of time, the following shall be out of scope:

- Cleaning up the auto generated boilerplate in `settings.py`. Yes, a lot is not needed, but it would take a fair bit of time to entirely remove.
- General Django new project best practices, such as overriding the default user model, making separate apps for every bit of functionality, setting models to UUIDs by default, or versioning the API.
- Authentication and security in general. The test API has none and this API will not be secured by one. Celery will just run on root. .env will not be configured for the secret. Debug will default to true.
- Substantial logging and general error handling beyond the problems specified in the task.
- Perfectly hostable project version. The URL is hardcoded to localhost rather than dealing with environment variables. It also will not run on Linux as I do not think most flavours support `host.docker.internal`.

## A Brief Architectural Discussion

The system works by the user (or potentially a programmic API call) triggering a Celery task via the endpoint `http://localhost:8000/extractor/trigger-task/` to go and get all the data from the target API. It starts with a multi threaded Celery task that moves iteratively through the available pages of animals after batching them. For each page, the animals are extracted and the IDs are saved and the data validated with a Pydantic `AnimalID` class. This step ensures that the data is used consistently throughout the application and ensures it is in the format expected.

The batches are each converted into their own Celery task. Within each task, multiple threads are used to call the API corresponding to the information for each animal. The Pydantic class `AnimalRaw` is used to validate that the data coming from the API is in the format expected. Then the raw data is transformed into `Animal` Pydantic classes that match the format expected by the `home` API and per the assignment.

The `Animal` classes are then posted to the `home` API in batches of 100. 

The server errors are handled by a `retry_api_call` wrapper that tries it again after a few seconds of delay if there is a failure. Threading helps to prevent the errors from delaying the overall process too much. The retry level and the timing of the delay are configurable.

The endpoint has an audit mode, which when the param `audit_mode` is set to true, it generates JSON files of the ids sent to the endpoint from the batches. There is a `verify_ids` function that checks to ensure every ID is present, as the multi threading makes verifying via the logs quite difficult.

There is logging to keep track of API failures, which would be a required task for most integrations to try and improve ETL extractor performance over time. 

### Why Django?
I chose Django because it is a highly suitable base for a startup product. It allows you to move quickly as many of the key decisions are made by default, has a robust community, and lets you build interfaces between the web and tasks easily.

### Why Celery?
ETL tasks take a long time to run, so better to not have it block the main process and best to parallelize it as much as possible.

### Why VCR? 
VCR is a wonderful library that allows the tests to use the actual API calls rather than mocks. This has two major benefits. First, it doesn't take long to make the cassettes as they are just recordings. Second, they are the actual API calls and in a real integration, they contain the same authentication mechanisms, header details, and errors that may be found in real API calls, but are often ignored in mocks.  

### The Merits of this Approach
What easy to use and maintain means differs greatly between people. To me, easy to use and maintain has a few requirements:

1. It runs reasonably quickly, allowing debugging in much shorter periods of time. That’s why there are multiple tasks and multiple threads. This is especially important with the unreliable base API, which is known to regularly lag or have errors as per the assignment.
2. It does not take a long time to set up. Docker containers make it pretty painless for anyone to install.
3. It uses technology I know. Django and Celery are technologies I am experienced with. Depending on the specifics, this may not be an ideal approach, but given the ambiguity of the assignment, it does the job and can serve as the base of an animal startup. 
4. It has logging to allow errors to be quickly identified. One of the most vexing challenges I have had with ETL is unclear logging, with vague “task failed” messages being the starting point for investigating how a pipeline failed. 
5. I can easily access reports and share reports with others as well as trigger the task from a dashboard (or perhaps via an API, such as when I worked at OneTrust). 
6. It is extensible. The pattern used here matches the integrations I built at OneTrust that had custom client base endpoints. 


### Alternatives Ruled Out

#### Cron job
The instructions say this should be the foundation of an animal based startup. I am biased, but where I worked previously, the data was part of a broader evidence collecting web app and merely putting it into a database with a cron job is less integrated than triggering it via a web app. Celery is a kind of cron job for Python web apps anyway. 

#### Script 
Explicitly excluded as per the instructions. 

#### Lambda/Cloud Function
Depending on how large the dataset is, this one is actually a popular option as quite a bit can fit within the free tier. I skipped this one as it wouldn't demonstrate much technical skill, but it would be a suitable answer for the scale of this task. It does get quite expensive at scale though. 

#### Single Threaded Task
This took quite a long time to run and was frustrating to test. I wanted it to go faster. 

#### Apache Airflow
Overkill for this scenario. 

#### Realtime Streaming 
The requirement from the assignment was for batches to the home endpoint, so batching in general seemed an appropriate approach. 

### How to Run it

1. Start up the other Docker container on port 3123. You can use a different port, but this project is hardcoded to that one. 
2. Run `docker-compose build` in the root directory
3. Run `docker-compose up django celery redis` in the root directory
4. Go to `http://localhost:8000/extractor/trigger-task/` to run it. You can set the param `audit_mode` to `True` to have it generate an auditable list of ids as proof that all ids were sent to the target endpoint. If you want to run this multiple times, make sure to delete the folder first or else there will be several runs of data and the verification will fail (this is meant as a quick and dirty verification, not a production system, so it has fewer guardrails).
5. Run the tests with `docker-compose run tests`
6. Verify the audited results by going to `leadpages_etl/app` and running `python3 verify_ids.py`. This requires `audit_mode` to have been added to a task and that audit mode not have been run multiple times without deleting the folder.

### Addressing Potential Concerns/Questions

#### Testing with a Live Endpoint
Normally you wouldn't include an endpoint with so much data in a test (I don't own this endpoint, nor can I configure it) so that choice is based on the limits of the provided API, but as endpoints, especially external endpoints can change, why wouldn't you want the earliest possible notice that something had changed? Including some (depending on whether they cost money and how much data they ingested) live endpoints at OneTrust let us see API changes quickly. 

#### Large Amounts of Test Data In Repo
I normally wouldn't do that. That is to make it easier for you to run the `verify_ids` code. 

#### This Requires Fairly Complex Setup for a Simple Task
There is a reasonable argument that this could be overkill for the task at hand. Maybe it is perfectly fine for it to be slow and take more time on the VPC in exchange for not needing additional infrastructure such as Celery. But on the other and, the amount of data could increase and it is nice to have the entire process finish relatively quickly. I also am trying to be hired, so need to prove I am capable of reasonably complicated things.