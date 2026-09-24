import json

from kafka import KafkaConsumer

from messaging.config import KafkaConfig

class FalconKafkaConsumer:

    def __init__(
            self,
            topic:str,
            group_id:str
    ):
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=KafkaConfig.BOOTSTRAP_SERVERS,
            group_id=group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda value:json.loads(value.decode("utf-8")),
        )

    def consumer(self):
        for message in self.consumer:
            yield message

    def commit(self):
        self.consumer.commit()

    def close(self):
        self.consumer.close()