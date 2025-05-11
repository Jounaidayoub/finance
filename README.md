# Project: Real-time Financial Data Surveillance and Alerting

## 1. Project Goal

To build a system that monitors real-time financial data streams (stocks, crypto), detects predefined anomalies (e.g., significant price drops within a short time window), triggers alerts, stores historical data for analysis, and provides an API and periodic reports.

## 2. Architecture Overview

The system follows a distributed, event-driven architecture using the following core components:
```mermaid
---
config:
      theme: redux
---
flowchart TD
        A(["Start"])
        A --> B{"Decision"}
        B --> C["Option A"]
        B --> D["Option B"]
```

*   **Data Ingestion:** Simulated financial data is published to a Kafka topic.
*   **Real-time Processing:** Celery workers consume data from Kafka, perform stateful anomaly detection, trigger alerts, and push data/anomalies to Elasticsearch.
*   **Data Storage:** Elasticsearch stores historical price data and detected anomalies for querying and analysis.
*   **Batch Processing:** Airflow schedules daily tasks to query Elasticsearch and generate summary reports.
*   **API Access:** FastAPI provides endpoints for users/clients to query historical data and anomalies from Elasticsearch.

## 3. Core Components & Technical Plan

### 3.1. Data Simulation (`generator.py`)

*   **Goal:** Simulate a stream of financial price updates.
*   **Implementation:**
    *   Read from sample data (e.g., `TSLA_1min_sample.csv`) or generate synthetic data.
    *   Format data as JSON objects (e.g., `{'symbol': 'TSLA', 'timestamp': '...', 'price': 150.50}`). *Action: Define exact JSON schema based on available data/requirements.*
    *   Connect to Kafka using `kafka-python` producer.
    *   Publish JSON messages to the `financial_prices` Kafka topic.
    *   Include realistic timing delays (e.g., `sleep(60)` for 1-minute data).
    *   *Future Enhancement:* Simulate multiple symbols.

### 3.2. Kafka

*   **Goal:** Act as the central, durable message bus for price data.
*   **Implementation:**
    *   Run Kafka brokers locally (using the downloaded distribution or Docker).
    *   Define topic(s):
        *   `financial_prices`: Main topic for incoming raw price updates. *(Consider partitioning for scalability)*.
        *   *(Optional)* `alerts`: Topic specifically for broadcasting detected anomaly events.
    *   *Action: Decide on final topic strategy and partitioning.*

### 3.3. Real-time Anomaly Detection (Python Celery)

*   **Goal:** Process price updates from Kafka in near real-time, detect anomalies, alert, and store.
*   **Implementation:**
    *   **Celery Setup:**
        *   Use Redis or RabbitMQ as the Celery message broker.
        *   Define Celery tasks in Python (e.g., `tasks.py`).
    *   **Kafka Consumer Bridge:** A script/process that:
        *   Consumes messages from the `financial_prices` Kafka topic using `kafka-python`.
        *   For each message, triggers a Celery task (e.g., `process_price_update.delay(message_data)`).
    *   **Celery Task (`process_price_update`):**
        *   Receives price data (JSON dictionary).
        *   **State Management:** Retrieve recent price history for the specific asset (e.g., last 1-5 minutes). *Action: Choose state management strategy (Redis recommended for scalability/resilience) and implement retrieval/update logic.*
        *   **Anomaly Logic:** Implement detection rules (e.g., calculate % change over the time window, compare to threshold like -10%). *Action: Define initial rule(s) and make them configurable if possible.*
        *   **Alerting:** If anomaly detected: Trigger alert mechanism. *Action: Define alert mechanism (e.g., log to file, call webhook, publish to `alerts` Kafka topic).*
        *   **Elasticsearch Indexing:** Push anomaly details and/or raw price data to Elasticsearch. *Action: Define Elasticsearch index structure and data to be stored.*
    *   **Celery Workers:** Run one or more Celery worker processes (`celery -A tasks worker ...`) to execute the tasks.

### 3.4. Data Storage (Elasticsearch)

*   **Goal:** Store historical data and anomalies for querying and analysis.
*   **Implementation:**
    *   Run Elasticsearch locally (e.g., via Docker).
    *   Define index mapping(s): Specify fields and data types (e.g., `timestamp` as date, `price` as float, `symbol` as keyword). Consider time-based indices (e.g., `financial_data-YYYY-MM-DD`).
    *   Celery tasks will use an Elasticsearch Python client (e.g., `elasticsearch-py`) to index data.
    *   *Action: Finalize index mapping and retention policy.*

### 3.5. Batch Reporting (Airflow) - *Future Scope*

*   **Goal:** Generate periodic summary reports (e.g., daily anomaly counts).
*   **Implementation:**
    *   Run Airflow locally (e.g., via Docker).
    *   Define a DAG (Directed Acyclic Graph) scheduled to run daily.
    *   Tasks within the DAG:
        *   Query Elasticsearch for relevant data (e.g., anomalies in the last 24 hours).
        *   Process data and format the report.
        *   Save/send the report. *Action: Define report content, format, and destination.*

### 3.6. API Access (FastAPI) - *Future Scope*

*   **Goal:** Provide an API for querying historical data and anomalies.
*   **Implementation:**
    *   Create a FastAPI Python application.
    *   Define API endpoints (e.g., `/anomalies`, `/prices`).
    *   Endpoints will query Elasticsearch based on request parameters (symbol, time range).
    *   Return results as JSON.
    *   *Action: Define specific API endpoints and query parameters.*

## 4. Setup and Running (Initial Steps)

1.  **Install Prerequisites:** Python 3.x, pip, Docker (recommended for Kafka, Elasticsearch, Redis).
2.  **Install Python Libraries:** `kafka-python`, `celery`, `redis`/`kombu` (for Celery broker), `elasticsearch-py`.
3.  **Start Infrastructure:**
    *   Run Zookeeper & Kafka Broker (using downloaded scripts or Docker).
    *   Run Elasticsearch (Docker recommended).
    *   Run Redis (Docker recommended, if chosen for Celery broker/state).
4.  **Create Kafka Topic:** Use `kafka-topics.sh` to create the `financial_prices` topic.
5.  **Run Generator:** `python generator.py`
6.  **Run Kafka-Celery Bridge:** `python kafka_bridge.py` (Needs to be created)
7.  **Run Celery Worker:** `celery -A tasks worker --loglevel=info` (Requires `tasks.py` with Celery app and task definitions)

## 5. Key Decisions / Actions Needed

*   Finalize JSON data schema for Kafka messages.
*   Choose and implement state management for Celery tasks (Redis recommended).
*   Define specific anomaly detection rule(s) and configurability.
*   Define alerting mechanism.
*   Define Elasticsearch index mapping and data storage strategy (raw vs. anomalies).
*   Define report requirements (content, format).
*   Define API endpoint requirements.
*   Decide on Kafka topic strategy (single vs. multiple).
