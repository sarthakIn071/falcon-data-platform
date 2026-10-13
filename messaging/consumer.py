import json

from kafka import KafkaConsumer
from kafka import TopicPartition
from kafka.structs import OffsetAndMetadata
from messaging.config import KafkaConfig

class FalconKafkaConsumer:

    def __init__(
            self,
            topic:str,
            group_id:str
    ):
        self._consumer = KafkaConsumer(
            topic,
            bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS,
            group_id=group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda value:json.loads(value.decode("utf-8")),
        )

    def poll(self, timeout_ms: int = 1000):
        return self._consumer.poll(timeout_ms=timeout_ms)

    def consume(self):
        for message in self._consumer:
            yield message

    def commit_batch(self, topic: str, partition: int, last_offset: int):
        topic_partition = TopicPartition(topic, partition)

        self._consumer.commit(
            offsets={
                topic_partition: OffsetAndMetadata(
                    offset=last_offset + 1,
                    metadata="",
                    leader_epoch=-1,
                )
            }
        )


    def commit(self):
        self._consumer.commit()

    def close(self):
        self._consumer.close()


