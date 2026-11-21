# Falcon Data Platform --- Architecture

**Document status:** Working baseline\
**Last reviewed:** 21 November 2026

## 1. Product vision

Falcon is a metadata-driven unified data ingestion and ETL platform.
Users should eventually configure pipelines through a UI rather than
write pipeline-specific Python code.

A pipeline definition describes its source, ingestion mode, format,
parser settings, schema, validation and data-quality rules,
transformations, destination, and execution settings. Falcon stores this
metadata and executes it through reusable components.

**Core principle:** build reusable engines and configuration contracts,
not one-off code for each pipeline.

## 2. Target architecture

``` text
Falcon UI (future)
    |
FastAPI backend
    |
Metadata/configuration repository (PostgreSQL)
    |
Pipeline orchestrator (planned)
    |
    +-- Batch: Falcon connectors
    +-- Streaming: Kafka
    +-- CDC: Debezium / Kafka Connect
    |
Common processing
    +-- Parse/decode
    +-- Schema validation
    +-- Data quality
    +-- Transformation
    +-- Serialization/load
    |
Storage and destinations
    +-- RustFS locally / S3 in cloud
    +-- Apache Iceberg
    +-- PostgreSQL, Redshift and other targets
```

Cross-cutting operations: - PostgreSQL tables for searchable execution
metadata, statuses, metrics, validation outcomes and quarantine
metadata. - Detailed structured application log files for diagnostic
detail and stack traces. - Object storage for large source/quarantine
payloads where appropriate, with references stored in PostgreSQL.

This is the target architecture. The orchestrator, UI, database-backed
operational logging and end-to-end Spark/Iceberg write path are not yet
complete.

## 3. Ingestion modes

### Batch

`Source -> Connector -> Parser -> Validation -> Data Quality -> Transformation -> Load`

Initial sources include REST APIs and files. Spark is intended for
scalable processing.

### Streaming

`Kafka -> Spark Structured Streaming -> Common processing -> Iceberg`

Kafka event infrastructure and a Spark runtime have been tested. The
complete streaming-to-Iceberg path remains to be implemented and
verified.

### CDC

`Database -> Debezium (Kafka Connect) -> Kafka -> Falcon CDC processing -> Iceberg`

Planned sources: PostgreSQL first, then Oracle, MySQL and SQL Server.
CDC must preserve operation type, keys, before/after images, source
metadata, ordering/offset context and replay semantics.

PostgreSQL logical replication settings are enabled in local Compose.
Debezium and the CDC end-to-end flow are not implemented yet.

## 4. Package responsibilities

  -----------------------------------------------------------------------
  Package                 Responsibility          Current understanding
  ----------------------- ----------------------- -----------------------
  `backend/`              FastAPI APIs            Foundation exists;
                                                  inspect before
                                                  extending

  `metadata/`             Metadata models,        Initial metadata schema
                          repositories and        exists
                          migrations              

  `connectors/`           Reusable source         Base, registry, demo
                          connectors              and REST work exists

  `messaging/`            Falcon events and Kafka Foundation exists
                          integration             

  `parsers/`              Format decoding and     JSON document/streaming
                          normalized parse        and NDJSON recovery
                          results                 implemented;
                                                  Avro/CSV/XML remain

  `validation/`           Schema validation and   Schema validation and
                          quarantine coordination local filesystem
                                                  quarantine exist

  `data_quality/`         Data-quality rules and  Existing engine/service
                          execution               foundation exists

  `processing/`           Reusable processing     Batch and Kafka batch
                          operations              processors exist;
                                                  common record processor
                                                  pending

  `spark/`                Distributed execution   Runtime/dependency
                          runtime                 smoke test passed

  `targets/`              Destination             Further implementation
                          writers/load engines    and review required

  `ingestion/`            Ingestion coordination  Existing package;
                                                  responsibilities need
                                                  review

  `orchestration/`        Pipeline lifecycle,     Not implemented
                          sequencing, retries     

  `ui/`                   Pipeline designer and   Not implemented
                          monitoring              
  -----------------------------------------------------------------------

Boundaries: - Parsers decode data; they do not query PostgreSQL or write
quarantine records. - Validators check records against configured
rules. - Processing coordinates reusable operations. - Orchestration
chooses and executes pipeline steps from metadata. -
Repositories/services own database persistence; processing classes
should not issue ad hoc SQL. - Parsers and output serializers/writers
are distinct.

## 5. Metadata-driven execution

PostgreSQL stores pipeline definitions and step configuration, including
JSONB configuration. A future orchestrator will load a pipeline,
validate its configuration, resolve implementations from registries,
pass typed configuration to components, execute steps in order, and
track each run and step.

Components must not read their own configuration directly from the
database. The repository/orchestrator loads metadata and passes typed
configuration to them.

A parser configuration describes how to interpret source data (format,
encoding, JSON mode, record path, schema, etc.). JSONB is a storage type
for configuration; it is not an input format or parser.

## 6. Parsing and record contracts

The current `ParseResult` represents one record outcome: - `record`:
normalized dictionary on success, otherwise `None`. - `record_number`:
source line/record position. - `raw_data`: original bytes. - `error`:
parsing error text, otherwise `None`. - `success`: derived property.

The recovery-oriented streaming method is intended for NDJSON (`LINES`)
mode. Existing `parse_stream()` remains fail-fast. Malformed JSON
arrays/documents are not assumed safely recoverable record by record.

Large files should be processed incrementally or in bounded batches.

## 7. Validation and quarantine

Keep failure stages distinct: - Parse failure: input could not be
decoded into the normalized record contract. - Validation failure:
parsing succeeded but the record failed schema rules. - DQ failure:
data-quality rules were violated. - Technical failure: connector,
infrastructure, code or destination execution failed.

Quarantine should preserve provenance: pipeline/run identifiers,
source/file details, record number, error stage, reason and source
payload/reference.

Current local quarantine writes JSON files. Target design is
PostgreSQL-backed quarantine metadata, with large raw payloads in
RustFS/S3 where appropriate and references in PostgreSQL. Migration is
pending.

## 8. Logging and observability: two complementary outputs

Falcon will use **both PostgreSQL operational tables and detailed log
files**. They serve different purposes; neither replaces the other.

### 8.1 PostgreSQL operational records

Use PostgreSQL for structured, queryable operational facts: -
Pipeline/step status, start/end timestamps and duration. - Counts: read,
parsed, valid, invalid, quarantined, written and rejected. -
Validation/DQ outcomes and error classifications. - Retry counts,
checkpoints and source/destination references. - Quarantine metadata and
references to payloads/log artifacts. - Correlation across pipeline,
run, step, source event and record where practical.

Proposed table names (not implemented; final schema requires design): -
`pipeline_runs` - `pipeline_step_runs` - `record_processing_logs`
(consider aggregation/sampling or bounded retention at high volume) -
`validation_results` - `quarantine_records` - `pipeline_metrics` -
`pipeline_errors`

Avoid one synchronous PostgreSQL insert per record if it creates a
throughput bottleneck. Use bounded batches, aggregation/sampling where
acceptable, and explicit retention/partitioning. Preserve required error
and quarantine evidence.

### 8.2 Detailed application log files

Use structured log files for diagnostic detail: - Component-level
INFO/WARNING/ERROR/DEBUG messages. - Exceptions and stack traces. -
Connector/API request diagnostics (never credentials or sensitive
payloads). - Parser and validation error context. - Spark
application/driver/executor diagnostics where available. - Retry
attempts, checkpoint decisions and recovery details.

Include correlation fields when known: - `timestamp`, `level`, `logger`,
`message` - `pipeline_id`, `run_id`, `step_run_id` - `source_name`,
`entity`, `event_id` or record number - `component`, `attempt`,
`error_code`, `exception_type`

Implementation direction: - Use Python `logging` with structured JSON
formatting. - Configure destinations, levels, rotation, retention and
file paths centrally. - Local development: configurable Falcon log
directory, size/time-based rotation and retention/compression policy. -
Production: container stdout/stderr and/or rotating files collected by a
log agent/platform; do not rely on ephemeral container storage as the
only copy. - PostgreSQL may store log-file/object references and run
summaries, not necessarily every diagnostic line. - Correlate files with
PostgreSQL records using `run_id` and `step_run_id`.

Never log passwords, API tokens, secret-bearing connection strings or
unrestricted sensitive records. Redact sensitive fields and prefer
payload references.

### 8.3 Payload and log-file storage

-   PostgreSQL: operational metadata and searchable summaries.
-   Log files/central collector: detailed diagnostics and stack traces.
-   RustFS/S3: large raw source or quarantined payloads where
    appropriate.
-   PostgreSQL: references, checksums, sizes, content type, retention
    metadata and correlation identifiers.

Exact retention periods, object layout and production log collector
remain to be decided.

## 9. Local development infrastructure

Known local services include PostgreSQL 16, Kafka, Zookeeper, RustFS,
Spark 4.1.4, Docker Compose and the Python virtual environment.

Preserve existing Docker volumes. Do not use `docker compose down -v` or
prune/delete volumes as routine cleanup.

## 10. Architecture decisions

1.  Falcon is metadata-driven; avoid duplicated pipeline-specific code.
2.  UI follows the core ingestion, processing, orchestration and
    operational foundations.
3.  Support batch, streaming and CDC ingestion modes.
4.  PostgreSQL is the metadata and operational system of record.
5.  Detailed diagnostic log files are also required; PostgreSQL and
    files have complementary roles.
6.  Store large payloads in object storage with PostgreSQL references
    where appropriate.
7.  Parsers do not access databases or quarantine stores directly.
8.  Processing components do not execute SQL directly; use
    repositories/services.
9.  Keep parsing, validation, DQ and technical failures distinct.
10. NDJSON recovery is line-oriented; do not promise safe recovery of
    malformed JSON arrays/documents.
11. Spark is the scale-out processing engine; lightweight Python
    components support local/control-plane operations.
12. PostgreSQL is the first CDC test source; Oracle, MySQL and SQL
    Server follow.

## 11. Open design questions

-   Operational logging/quarantine schemas, indexes and retention.
-   Log rotation, naming, compression, retention and production
    collection.
-   High-volume record outcomes: individual, aggregated, sampled or
    tiered.
-   Payload/object storage layout and lifecycle.
-   Avro, CSV and XML parser contracts.
-   Schema registry and schema-evolution implementation.
-   Orchestrator execution, retries, checkpoints and idempotency.
-   Spark-to-Iceberg-to-RustFS end-to-end write design.
-   CDC envelope normalization and delete/upsert semantics.
