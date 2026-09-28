CREATE TABLE falcon_metadata.dq_rule_sets (
    rule_set_id BIGSERIAL PRIMARY KEY,
    rule_set_name VARCHAR(150) NOT NULL,
    description TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_dq_rule_set_name_version
        UNIQUE (rule_set_name, version)
);


CREATE TABLE falcon_metadata.dq_rules (
    rule_id BIGSERIAL PRIMARY KEY,
    rule_set_id BIGINT NOT NULL,
    field_name VARCHAR(150) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'ERROR',
    rule_value VARCHAR(500),
    rule_values JSONB,
    description TEXT,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_dq_rule_rule_set
        FOREIGN KEY (rule_set_id)
        REFERENCES falcon_metadata.dq_rule_sets(rule_set_id)
        ON DELETE CASCADE
);