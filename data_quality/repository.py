import psycopg

from data_quality.rules import DQRule, DQRuleSet


class DQRuleRepository:
    """
    Reads Data Quality rules from Falcon metadata DB.
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def get_rule_set(self, rule_set_id: int) -> DQRuleSet:
        with psycopg.connect(self.connection_string) as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT
                        rule_set_id,
                        rule_set_name,
                        description,
                        version,
                        status
                    FROM falcon_metadata.dq_rule_sets
                    WHERE rule_set_id = %s
                    """,
                    (rule_set_id,),
                )

                rule_set_row = cursor.fetchone()

                if rule_set_row is None:
                    raise ValueError(
                        f"DQ rule set not found: {rule_set_id}"
                    )

                cursor.execute(
                    """
                    SELECT
                        rule_id,
                        field_name,
                        rule_type,
                        severity,
                        rule_value,
                        rule_values,
                        description,
                        enabled
                    FROM falcon_metadata.dq_rules
                    WHERE rule_set_id = %s
                      AND enabled = TRUE
                    ORDER BY rule_id
                    """,
                    (rule_set_id,),
                )

                rule_rows = cursor.fetchall()

        rules = [
            DQRule(
                rule_id=row[0],
                field_name=row[1],
                rule_type=row[2],
                severity=row[3],
                rule_value=row[4],
                rule_values=row[5] or [],
                description=row[6],
                enabled=row[7],
            )
            for row in rule_rows
        ]

        return DQRuleSet(
            rule_set_id=rule_set_row[0],
            rule_set_name=rule_set_row[1],
            description=rule_set_row[2],
            version=rule_set_row[3],
            status=rule_set_row[4],
            rules=rules,
        )