import json

from kafka import KafkaProducer

from messaging.config import KafkaConfig
from messaging.event import FalconEvent

class FalconKafkaProducer:

    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers = KafkaConfig.BOOTSTRAP_SERVERS,
            value_serializer=lambda value: json.dumps(
                value
            ).encode("utf-8"),

            key_serializer = lambda value:(
                value.encode("utf-8")
                if value
                else None
            ),
        )

    def publish(
            self,
            topic:str,
            event:FalconEvent,
            key:str | None = None,
    ):
        future = self.producer.send(
            topic,
            key=key,
            value=event.model_dump(mode="json"),
        )

        result = future.get(
            timeout = KafkaConfig.DEFAULT_TIMEOUT_MS/1000
        )

        return {
            "topic": result.topic,
            "partition":result.partition,
            "offset":result.offset
        }

    def flush(self):
        self.producer.flush()

    def close(self):
        self.producer.close()