# Falcon Data Platform --- Current Status

**Last reviewed:** 21 November 2026\
**Status basis:** Previous development session and test output.
Re-verify the local working tree before changes.

## 1. Current position

Falcon has a working local development foundation and implementations
across connectors, Kafka, JSON parsing, validation, batch processing,
Spark runtime and RustFS.

The next major gap is connecting these components through a common
processing/orchestration path and centralized operational persistence.

## 2. Latest known Git checkpoint

Last recorded branch: `main`

Last recorded clean status:

``` text
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

Last recorded commits:

``` text
630a10a chore: enable PostgreSQL logical replication for CDC
b87032b feat: add streaming JSON parser and performance benchmarks
ec400b7 feat: add Spark and RustFS data lake runtime
```

These are last known values, not a live inspection of the current
working tree.

## 3. Local runtime

Known services: - PostgreSQL 16 (`falcon-postgres`) - Kafka
(`falcon-kafka`) - Zookeeper (`falcon-zookeeper`) - RustFS
(`falcon-rustfs`) - Spark 4.1.4 custom runtime

Known endpoints: - Kafka host: `localhost:9092` - Kafka from Docker:
`kafka:29092` - RustFS S3 API: `http://localhost:9000` - RustFS console:
`http://localhost:9001` - PostgreSQL host: `localhost:5432`

Local RustFS bucket: `falcon-warehouse`.

PostgreSQL logical replication is configured with `wal_level=logical`,
`max_wal_senders=10` and `max_replication_slots=10`. A separate CDC
database and Debezium connector have not yet been created.

**Data safety:** never run `docker compose down -v`,
`docker volume prune` or delete existing
PostgreSQL/Kafka/Zookeeper/RustFS volumes as routine cleanup.

## 4. Implemented components

### Connectors and messaging

-   Connector base framework and registry.
-   Demo connector and REST connector foundation.
-   FalconEvent model.
-   Kafka topic and event testing foundation.

### Processing

-   Generic `BatchBuilder`.
-   `DQBatchProcessor`.
-   `KafkaBatchProcessor`.
-   Common parse-to-validation `RecordProcessor` is not implemented.

### Parsers

-   `BaseParser`.
-   `ParserConfig` and `SchemaEvolutionConfig`.
-   `ParserRegistry` with JSON registered.
-   JSON document parsing for objects and arrays.
-   Nested JSON extraction through `record_path`.
-   Incremental JSON array/document streaming using `ijson`.
-   NDJSON streaming, blank-line skipping and fail-fast behavior.
-   `ParseResult` result model.
-   `parse_stream_with_errors()` for NDJSON recovery.
-   Avro config/dependencies exist, but Avro parser implementation
    remains pending.
-   CSV and XML parsers remain pending.

### Validation and quarantine

-   `SchemaValidator` and `ValidationRuleSet`.
-   `ValidationService.validate_record()`.
-   `ValidationService.validate_event()`.
-   `QuarantineStore` writes record/file JSON to local filesystem.
-   `QuarantineRecord` includes `record_number`, `error_stage`,
    `raw_data`.
-   `ValidationService.quarantine_parse_error()` exists and has a
    focused test.
-   Database-backed quarantine is pending.

### Spark and storage

-   Spark 4.1.4 runtime smoke test passed.
-   Spark Kafka and Iceberg dependencies resolved.
-   RustFS is running locally and bucket was created.
-   Full Spark write/read to Iceberg on RustFS is pending.

## 5. Recent test evidence

  Test run                                           Result
  --------------------------------------------- -----------
  Validation/quarantine focused tests              6 passed
  JSON stream + recovery tests                    16 passed
  Earlier full suite, before latest additions     90 passed

A full-suite run after all recent changes has not been recorded. Run:

``` powershell
python -m pytest -v
```

and update this document with the actual result.

## 6. Operational logging decision

**Agreed requirement:** Falcon must have both PostgreSQL operational
tables and detailed log files.

### PostgreSQL operational tables

Store searchable structured information: - Pipeline runs and step
runs. - Processing counts and outcomes. - Validation and DQ results. -
Quarantine metadata. - Error classifications and metrics. - References
to detailed log artifacts and payloads.

Proposed table names (not implemented): - `pipeline_runs` -
`pipeline_step_runs` - `record_processing_logs` - `validation_results` -
`quarantine_records` - `pipeline_metrics` - `pipeline_errors`

### Detailed log files

Store diagnostic detail: - Structured JSON log messages. -
Component-level events and stack traces. - Connector, parser, Spark and
retry diagnostics. - Correlation identifiers: `pipeline_id`, `run_id`,
`step_run_id`.

Development should use configurable rotating local log files. Production
should use container stdout/stderr and/or files collected by a log
agent/central logging platform. Rotation, retention and production
collection configuration remain to be designed.

Large raw payloads should preferably live in RustFS/S3, with references
and metadata in PostgreSQL. Do not log credentials or unrestricted
sensitive payloads.

## 7. Important design boundaries

-   Parser does not connect to PostgreSQL or quarantine storage.
-   Validation service coordinates validation/quarantine behavior.
-   Processing coordinates reusable record operations.
-   Orchestrator executes metadata-defined pipeline steps and owns
    lifecycle/retries.
-   Repositories/services own PostgreSQL persistence.
-   PostgreSQL operational records and detailed log files are
    complementary.
-   Large payloads should not be copied into every operational log row.
-   Parsing, validation, DQ and technical errors must remain
    distinguishable.

## 8. Immediate next tasks

1.  Inspect current metadata migrations and tables.
2.  Design operational logging and quarantine database schema.
3.  Define detailed log-file format, correlation fields, rotation and
    retention.
4.  Implement centralized structured logging configuration.
5.  Implement PostgreSQL repositories/services for run/step status,
    metrics and quarantine metadata.
6.  Then implement `RecordProcessor` against the agreed service
    contracts.
7.  Run the full test suite and update this status file.

## 9. Not yet implemented

-   `RecordProcessor`.
-   Operational logging tables/repositories.
-   Database-backed quarantine.
-   Centralized detailed rotating log-file configuration.
-   Avro, CSV and XML parser implementations.
-   Schema evolution checker.
-   Generic transformation engine integration.
-   Full Spark → Iceberg → RustFS end-to-end path.
-   Debezium/Kafka Connect CDC.
-   Pipeline orchestrator and scheduler.
-   UI pipeline designer and monitoring dashboard.
