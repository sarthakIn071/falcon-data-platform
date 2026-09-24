4.4 Create sources
CREATE TABLE falcon_metadata.sources (
    source_id BIGSERIAL PRIMARY KEY,

    source_name VARCHAR(100) NOT NULL UNIQUE,

    source_type VARCHAR(50) NOT NULL,

    description TEXT,

    connection_config JSONB,

    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

Examples of source_type:

REST_API
JSON
XML
CSV
EXCEL
POSTGRES
ORACLE
S3
SFTP
DEBEZIUM
4.5 Create targets
CREATE TABLE falcon_metadata.targets (
    target_id BIGSERIAL PRIMARY KEY,

    target_name VARCHAR(100) NOT NULL UNIQUE,

    target_type VARCHAR(50) NOT NULL,

    connection_config JSONB,

    target_schema VARCHAR(100),

    target_table VARCHAR(100),

    load_mode VARCHAR(30),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

Examples:

POSTGRES
S3
REDSHIFT

Load modes:

INSERT
UPSERT
MERGE
4.6 Create pipelines

This is one of the most important Falcon tables.

CREATE TABLE falcon_metadata.pipelines (
    pipeline_id BIGSERIAL PRIMARY KEY,

    pipeline_name VARCHAR(150) NOT NULL UNIQUE,

    description TEXT,

    source_id BIGINT NOT NULL,

    target_id BIGINT NOT NULL,

    ingestion_mode VARCHAR(20) NOT NULL,

    transport_type VARCHAR(30) NOT NULL DEFAULT 'KAFKA',

    kafka_topic VARCHAR(250),

    partition_key VARCHAR(150),

    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',

    version INTEGER NOT NULL DEFAULT 1,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_pipeline_source
        FOREIGN KEY (source_id)
        REFERENCES falcon_metadata.sources(source_id),

    CONSTRAINT fk_pipeline_target
        FOREIGN KEY (target_id)
        REFERENCES falcon_metadata.targets(target_id)
);

Notice:

ingestion_mode

can be:

BATCH
STREAM
HYBRID

And:

transport_type

can initially be:

KAFKA
DIRECT

This preserves the architecture we designed.

4.7 Create pipeline_steps
CREATE TABLE falcon_metadata.pipeline_steps (
    step_id BIGSERIAL PRIMARY KEY,

    pipeline_id BIGINT NOT NULL,

    step_name VARCHAR(100) NOT NULL,

    step_type VARCHAR(50) NOT NULL,

    step_order INTEGER NOT NULL,

    configuration JSONB,

    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_step_pipeline
        FOREIGN KEY (pipeline_id)
        REFERENCES falcon_metadata.pipelines(pipeline_id)
        ON DELETE CASCADE,

    CONSTRAINT uq_pipeline_step_order
        UNIQUE (pipeline_id, step_order)
);

Possible step_type:

EXTRACT
KAFKA_PUBLISH
VALIDATE
DATA_QUALITY
TRANSFORM
RECONCILE
LOAD

This allows a pipeline to look like:

1 EXTRACT
2 KAFKA_PUBLISH
3 VALIDATE
4 DATA_QUALITY
5 TRANSFORM
6 RECONCILE
7 LOAD
4.8 Create pipeline_runs

Every execution gets a unique run_id.

CREATE TABLE falcon_metadata.pipeline_runs (
    run_id UUID PRIMARY KEY,

    pipeline_id BIGINT NOT NULL,

    status VARCHAR(30) NOT NULL,

    start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    end_time TIMESTAMP,

    records_extracted BIGINT DEFAULT 0,

    records_published BIGINT DEFAULT 0,

    records_processed BIGINT DEFAULT 0,

    records_valid BIGINT DEFAULT 0,

    records_dq_failed BIGINT DEFAULT 0,

    records_loaded BIGINT DEFAULT 0,

    records_failed BIGINT DEFAULT 0,

    error_message TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_run_pipeline
        FOREIGN KEY (pipeline_id)
        REFERENCES falcon_metadata.pipelines(pipeline_id)
);

This will eventually power the UI statistics:

Records Extracted
Records Published
Records Valid
DQ Failed
Records Loaded
Records Failed
4.9 Create pipeline_step_runs
CREATE TABLE falcon_metadata.pipeline_step_runs (
    step_run_id BIGSERIAL PRIMARY KEY,

    run_id UUID NOT NULL,

    step_id BIGINT NOT NULL,

    status VARCHAR(30) NOT NULL,

    start_time TIMESTAMP,

    end_time TIMESTAMP,

    input_count BIGINT DEFAULT 0,

    output_count BIGINT DEFAULT 0,

    error_count BIGINT DEFAULT 0,

    error_message TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_step_run
        FOREIGN KEY (run_id)
        REFERENCES falcon_metadata.pipeline_runs(run_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_step_definition
        FOREIGN KEY (step_id)
        REFERENCES falcon_metadata.pipeline_steps(step_id)
);

This will allow us to display:

Pipeline Run

Extract        10,000   ✓
Kafka          10,000   ✓
Validation      9,980   ✓
DQ              9,950   ✓
Transform       9,950   ✓
Load            9,950   ✓
4.10 Verify the database

Run:

\dt falcon_metadata.*

You should see:

sources
targets
pipelines
pipeline_steps
pipeline_runs
pipeline_step_runs

Then:

\d falcon_metadata.pipelines

Check the columns.