# Falcon Data Platform --- Roadmap

**Document status:** Working plan\
**Last reviewed:** 21 November 2026

Status labels reflect evidence available at this review date. Refresh
after inspecting the repository and running tests.

-   **Done:** implemented and verified.
-   **Partial:** foundation exists; end-to-end capability incomplete.
-   **Planned:** not implemented.
-   **Design:** direction agreed; implementation/schema pending.

## Phase 0 --- Local foundation

  -----------------------------------------------------------------------
  Work item               Status                  Notes
  ----------------------- ----------------------- -----------------------
  GitHub repository and   Done                    
  local Python                                    
  environment                                     

  Docker Compose:         Done                    Preserve existing
  PostgreSQL, Kafka,                              volumes
  Zookeeper                                       

  Metadata database and   Partial                 Review migrations
  initial tables                                  before extending

  Kafka event model/topic Partial                 Foundation exists
  smoke tests                                     

  RustFS local object     Done                    Bucket created
  storage                                         

  Spark runtime           Done                    Spark 4.1.4 smoke test
                                                  passed

  Spark Kafka/Iceberg     Done                    Dependency smoke test
  dependencies                                    passed

  Full Spark → Iceberg →  Planned                 Not verified end-to-end
  RustFS write path                               
  -----------------------------------------------------------------------

## Phase 1 --- Reusable ingestion and parser foundation

  -----------------------------------------------------------------------
  Work item               Status                  Notes
  ----------------------- ----------------------- -----------------------
  Connector base and      Done                    
  registry                                        

  Demo connector          Done                    

  REST/JSON connector     Partial                 Existing
                                                  implementation;
                                                  production
                                                  retry/pagination review
                                                  remains

  Falcon event framework  Partial                 Event model and Kafka
                                                  integration foundation

  JSON document parser    Done                    Objects, arrays and
                                                  record path

  JSON streaming parser   Done                    Incremental parsing

  NDJSON recovery parser  Done                    Per-line error results;
                                                  fail-fast method
                                                  retained

  Common `ParseResult`    Done                    Record, record number,
  contract                                        raw bytes and error

  Avro parser             Planned                 Config/dependencies
                                                  exist; parser not
                                                  complete

  CSV/XML parsers         Planned                 

  Cross-format parser     Partial                 JSON tests exist
  contract tests                                  
  -----------------------------------------------------------------------

## Phase 2 --- Validation, quarantine and processing integration

  -----------------------------------------------------------------------
  Work item               Status                  Notes
  ----------------------- ----------------------- -----------------------
  Schema validator and    Done                    
  rule models                                     

  Validation service      Done                    

  Local filesystem        Done                    Current implementation
  quarantine                                      

  Quarantine parsing      Done                    `record_number`,
  metadata                                        `raw_data`,
                                                  `error_stage` added

  Parsing-error           Done                    Tested; uses local
  quarantine method                               `QuarantineStore`

  `RecordProcessor`       Planned                 Connect parser results
                                                  to
                                                  validation/quarantine

  Processing outcome      Planned                 Distinguish parse,
  model                                           validation and success
                                                  outcomes

  Batch integration       Planned                 Reuse existing batch
                                                  abstractions

  DQ integration into     Partial                 DQ batch processor
  common record flow                              exists; end-to-end
                                                  integration pending
  -----------------------------------------------------------------------

## Phase 3 --- Operational persistence and observability

**High priority. Design agreed; implementation pending.**

### PostgreSQL operational metadata

Proposed tables (names provisional): - `pipeline_runs` -
`pipeline_step_runs` - `record_processing_logs` - `validation_results` -
`quarantine_records` - `pipeline_metrics` - `pipeline_errors`

Tasks: 1. Inspect existing metadata migrations/tables. 2. Define
identifiers and relationships for pipeline, run, step, source, event and
record. 3. Define statuses, timestamps, durations and counters. 4.
Design quarantine metadata and payload references. 5. Define batch-write
strategy for high-volume outcomes. 6. Implement repositories/services
and tests. 7. Define indexes, retention, partitioning and cleanup.

### Detailed log files

Tasks: 1. Central logging configuration. 2. Structured JSON log records.
3. Correlation fields: `pipeline_id`, `run_id`, `step_run_id`, component
and error context. 4. Configurable local rotating log files. 5.
Rotation, compression, retention and log-directory settings. 6.
Production stdout/stderr and log-agent/central collection approach. 7.
Secret and sensitive-payload redaction. 8. Log references/correlation
metadata where useful.

### Storage separation

-   PostgreSQL: structured operational metadata and searchable
    summaries.
-   Log files/central collector: detailed diagnostic events and stack
    traces.
-   RustFS/S3: large raw/quarantined payloads where appropriate.
-   PostgreSQL: references to payloads and log artifacts.

## Phase 4 --- Common processing and Data Lake engine

1.  Complete `RecordProcessor`.
2.  Connect parsing, schema validation and quarantine.
3.  Connect DQ processing.
4.  Implement reusable transformation contracts.
5.  Implement output serializers separately from parsers.
6.  Implement generic Spark execution interfaces.
7.  Write/read Iceberg tables on RustFS locally.
8.  Verify Kafka → Spark Structured Streaming → Iceberg.
9.  Add schema evolution and compatibility checks.
10. Add integration tests and performance benchmarks.

Output formats under consideration: JSON, CSV, Parquet and Avro. Begin
with the local Data Lake path and keep destinations extensible.

## Phase 5 --- CDC framework

First source: PostgreSQL.

Target flow:
`PostgreSQL -> Debezium PostgreSQL connector -> Kafka -> Falcon CDC processing -> Spark -> Iceberg`

1.  Create a separate CDC test database; do not modify Falcon metadata
    DB.
2.  Verify logical replication and replication privileges/slots.
3.  Add Kafka Connect runtime.
4.  Deploy Debezium PostgreSQL connector.
5.  Verify initial snapshot and ongoing changes.
6.  Test INSERT, UPDATE and DELETE.
7.  Preserve keys, before/after, operation, source metadata and offsets.
8.  Implement replay, restart, duplicate handling and checkpointing.
9.  Integrate CDC with Spark/Iceberg.
10. Extend to Oracle, MySQL and SQL Server.

PostgreSQL logical replication settings are enabled in local Compose.
Debezium is not installed/configured.

## Phase 6 --- Orchestration and backend APIs

1.  Define pipeline step contracts and registry.
2.  Implement orchestrator that loads pipeline metadata.
3.  Execute steps in configured order.
4.  Track pipeline and step runs in PostgreSQL.
5.  Implement retries, timeouts, cancellation and recovery.
6.  Define idempotency and checkpoint semantics.
7.  Expose pipeline CRUD and execution APIs through FastAPI.
8.  Add scheduling after execution lifecycle is stable.

Orchestration controls lifecycle and sequence; `processing/` implements
reusable operations.

## Phase 7 --- UI and production readiness

-   Visual pipeline designer and configuration forms.
-   Source/target catalog.
-   Schema and rule configuration.
-   Run history, logs, metrics and quarantine views.
-   Authentication and authorization.
-   Secrets management.
-   Deployment automation and CI/CD.
-   Resource controls, scalability, alerting and runbooks.

## Recommended immediate sequence

1.  Review current repository and metadata migrations.
2.  Finalize architecture and roadmap baseline.
3.  Inspect current PostgreSQL metadata tables.
4.  Design operational logging and quarantine persistence.
5.  Implement centralized structured file logging.
6.  Implement PostgreSQL repositories/services for operational metadata.
7.  Implement `RecordProcessor` against the service contracts.
8.  Run the full test suite and refresh status.
9.  Continue parser/processing and Spark/Iceberg integration.

Do not start CDC or UI work yet.

## Milestone discipline

At each meaningful milestone: - Run focused tests, then full tests where
appropriate. - Record actual test counts and benchmark evidence. -
Update `CURRENT_STATUS.md` and this roadmap. - Commit a clean Git
checkpoint. - Never mark a design-only item as implemented.
