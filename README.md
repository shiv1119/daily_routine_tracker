<div align="center" id="top"> 
  <img src="./.github/app.gif" alt="Promotion-Engine" />

  &#xa0;
</div>

<h1 align="center">Daily Routine Tracker</h1>

<p align="center">
  <img alt="Github top language" src="https://img.shields.io/github/languages/top/shiv1119/daily_routine_tracker?color=56BEB8">

  <img alt="Github language count" src="https://img.shields.io/github/languages/count/shiv1119/daily_routine_tracker?color=56BEB8">

  <img alt="Repository size" src="https://img.shields.io/github/repo-size/shiv1119/daily_routine_tracker?color=56BEB8">

  <img alt="License" src="https://img.shields.io/github/license/shiv1119/daily_routine_tracker?color=56BEB8">

  <img alt="Github issues" src="https://img.shields.io/github/issues/shiv1119/daily_routine_tracker?color=56BEB8" />

  <img alt="Github forks" src="https://img.shields.io/github/forks/shiv1119/daily_routine_tracker?color=56BEB8" />

  <img alt="Github stars" src="https://img.shields.io/github/stars/shiv1119/daily_routine_tracker?color=56BEB8" />
</p>

<!-- Status -->

<h4 align="center"> 
	Daily Routine Tracker
</h4> 

<hr>

<p align="center">
  <a href="#dart-Objective">Objective</a> &#xa0; | &#xa0; 
  <a href="#rocket-technologies">Technologies</a> &#xa0; | &#xa0;
  <a href="#white_check_mark-requirements">Requirements</a> &#xa0; | &#xa0;
  <a href="#checkered_flag-starting">Starting</a> &#xa0; | &#xa0;
  <a href="#checkered_flag-Curl-examples">Curl Examples</a> &#xa0; | &#xa0;
  <a href="#checkered_flag-Reflection-Rationale">Reflection and Rationale</a> &#xa0; | &#xa0;
  <a href="https://github.com/shiv1119" target="_blank">Author</a>
</p>

<br>

## :dart: Objective ##

Design and implement a small REST microservice that selects the most appropriate in‑game promotion for a player based on configurable business rules.

## :rocket: Technologies ##

The following tools were used in this project:

- [Python](https://www.python.org/)
- [Fast API](https://fastapi.tiangolo.com/)
- [Docker](https://www.docker.com/)
- [Pytest](https://docs.pytest.org/en/stable/)

## :white_check_mark: Requirements ##

Before starting :checkered_flag:, you need to have [Git](https://git-scm.com) and [Python](https://www.python.org/) installed.

## :checkered_flag: Starting ##

## Setup using Docker (Easy and Recommended but make sure docker installed)

```bash
# Clone this project
$ git clone https://github.com/shiv1119/Promotion-Engine.git

# Access
$ cd Promotion-Engine

# Run the project
$ docker-compose up --build

# The server will initialize in the <http://127.0.0.1:8000/>
```


## Setup without docker
```bash
# Clone this project
$ git clone https://github.com/shiv1119/Promotion-Engine.git

# Access
$ cd Promotion-Engine

# Install dependencies
$ pip install -r requirements.txt

# Create virtual environment
$ python -m venv venv

# Activate Virtual environment
$ venv\Scripts\Activate         (on windows)
$ source venv/bin/activate       (on linux or macos)

# Run Tests
$ pytest --cov=. or pytest

# Run the project
$ cd app
$ uvicorn main:app --reload

# The server will initialize in the <http://localhost:5000 or http://127.0.0.1:8000>
```
## :checkered_flag: Curl-examples ##

1. Promotion - `POST api/promotion`
```bash
  $ curl -X 'POST' \
      'http://127.0.0.1:8000/api/promotion' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "level": 12,
      "spend_tier": "high",
      "country": "US",
      "days_since_last_purchase": 1,
      "ab_bucket": "A"
    }
    '
```
    Status code - 200
    Response Body 
    {
      "promotion": {
        "type": "bonus_cash",
        "value": 10,
        "item": null,
        "weight": 1
      }
    }

2. Reload Rules Data `POST api/reload`
```bash
  $ curl -X 'POST' \
    'http://127.0.0.1:8000/api/reload' \
    -H 'accept: application/json' \
    -d ''
```
    Status code = 200
    Response body
    {
      "status": "Rules reloaded successfully"
    }

3. Reload Rules Data `GET api/metrics`
```bash
	$ curl -X 'GET' \
    'http://127.0.0.1:8000/api/metrics' \
    -H 'accept: application/json'
```
    Status code - 200	
    Response body

    {
      "total_evaluations": 1,
      "hits": 1,
      "misses": 0,
      "avg_latency_ms": 0.04
    }

## :checkered_flag: Reflection-Rationale ##

### A. Design Choices
1. **Rule Representation & Storage** - I have chose to implement promotion rules using Pydantic Base Model classes for schema validation, type, safety and one of important for automatic documentation via Fast API. Rules are loaded from a YAML files into in-memory storage for fast access and evaluation.

2. **Routing and API Structure** -  I used Fast API ofr its lightening speed, simplicity, and support for type hints, which enables clean auto generated docs and better developer experience. Routes are organised using API Router to separate business logic from API interface for maintainability.

3. **Evaluation Logic** - I implemented rules evaluation in separated and dedicated service to encapsulate the logic and keep the route handler clean. A linear search (Takes O(n) time) is used to match rules by priority, which is acceptable for small rule sets and keeps the implementation simple.

4. **Testing** - I chose pytest and TestClient from FastAPI to write integration-style endpoint tests. Fixtures were used to reload rules before tests to ensure isolation and repeatability.

### B. Trade-Offs

1. **Simplicity vs Performance** - I used simple linear rule matching approach rather than using a rule engine library (like Drools or durable_rules) or indexing rules. While this will give less throughput for large scale rules but it keeps the implementation easy to understand and debug. 

Later if needed then rules indexing or a rule engine library can be added easily.

2. **YAML-Based rules management** - YAML simplifies rule updates and encourages business-friendly configurations but iyt lacks runtime validation beyond structures like logical overlaps or say conflicting conditions.

3. **In-memory rule storage** - As in memory avoids database dependency and supports fast reads, but means changes are not persistent unless saved manually.

### C. Areas of Uncertainty - 
1. - I was unsure whether to prefer promotion weight as ranking factor over priority. I choose priority for evaluation(lower priority = high precedence) and considered weight only for future probabilistic selection.

2. Initially, I wasn’t sure whether to treat None values in player attributes (e.g., missing country) as wildcards or disqualify the rule. I ultimately chose a strict match approach — if the rule expects a value and the player lacks it, the rule won't match.

### D. AI Assistance

Yes, I used ChatGPT as a coding assistant. Here's how:

1. I used ChatGPT to help me understand how to structure the Fast API routes, YAML Loading and how to handle rule evaluation cleanly using Python classes.

2. I used it to generate the initial version of the evaluate_rules function. I then modified it to support time-window conditions, AB Bucket and added latency tracking.

## Design Pattern Used

1. **Strategy Pattern** -  encapsulate different rule-matching conditions (e.g., country match, spend tier match, level range) and apply them per rule dynamically.

2. **Singleton Pattern** - The RuleStorage class is instantiated once and used globally to hold all the loaded rules.

3. **Factory Pattern** - Converts data from YAML into Rule objects using Rule(**r), which is essentially factory-style instantiation based on structured input.

4. **Decorator Pattern via Fast API** - FastAPI uses decorators to attach metadata and behavior to route handlers (authentication, response models, etc.)

5. **Null Object Pattern** - Rules evaluation returns None when no rules matches.

6. **Data Transfer Object Pattern** - Pydantic models define structured inputs/outputs and ensure data integrity between client and server.

---


Made with :heart: by <a href="https://github.com/shiv1119" target="_blank">Shiv Nandan Verma</a>

&#xa0;
<a href="#top">Back to top</a>
