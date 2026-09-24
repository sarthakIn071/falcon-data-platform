import os

class KafkaConfig:

    BOOTSTRAP_SERVERS = os.getenv(
        "KAFKA_BOOTSTRAP_SERVERS",
        "localhost:9092"
    )

    DEFAULT_TIMEOUT_MS = int(
        os.getenv("KAFKA_TIMEOUT_MS","10000")
    )