import json

from kafka import KafkaProducer
from kafka.serializer import Serializer
from messaging.config import KafkaConfig
from messaging.event import FalconEvent




class FalconValueSerializer(Serializer):
    """Serialize Kafka message values to JSON bytes."""

    def serialize(self, topic, headers, value):
        if value is None:
            return None

        return json.dumps(value).encode("utf-8")


class FalconKeySerializer(Serializer):
    """Serialize Kafka message keys to UTF-8 bytes."""

    def serialize(self, topic, headers, value):
        if value is None:
            return None

        return value.encode("utf-8")


        
class FalconKafkaProducer:

    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers = KafkaConfig.BOOTSTRAP_SERVERS,
            value_serializer=FalconValueSerializer(),
            key_serializer = FalconKeySerializer(),
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