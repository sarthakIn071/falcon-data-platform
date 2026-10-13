
from messaging.consumer import FalconKafkaConsumer
from processing.batch import BatchBuilder
from processing.models import KafkaBatch, KafkaRecord


class KafkaBatchProcessor:
    def __init__(
        self,
        consumer: FalconKafkaConsumer,
        batch_size: int,
        timeout_seconds: float = 30.0,
    ):
        self.consumer = consumer
        self.batch_size = batch_size
        self.timeout_seconds = timeout_seconds

        self.batch_builders: dict[
            tuple[str, int], BatchBuilder[KafkaRecord]
        ] = {}

    def _get_batch_builder(
        self,
        topic: str,
        partition: int,
    ) -> BatchBuilder[KafkaRecord]:
        key = (topic, partition)

        if key not in self.batch_builders:
            self.batch_builders[key] = BatchBuilder[KafkaRecord](
                batch_size=self.batch_size,
                timeout_seconds=self.timeout_seconds,
            )

        return self.batch_builders[key]

    def commit_batch(self, batch: KafkaBatch):
        self.consumer.commit_batch(
            topic=batch.topic,
            partition=batch.partition,
            last_offset=batch.last_offset,
        )

    def _create_batch(self, records: list[KafkaRecord]) -> KafkaBatch:
        if not records:
            raise ValueError("Cannot create KafkaBatch from empty records")

        topics = {record.topic for record in records}
        partitions = {record.partition for record in records}

        if len(topics) != 1 or len(partitions) != 1:
            raise ValueError(
                "Kafka batch must contain records from one topic and partition"
            )

        return KafkaBatch(
            records=[record.value for record in records],
            topic=records[0].topic,
            partition=records[0].partition,
            first_offset=records[0].offset,
            last_offset=records[-1].offset,
        )

    def process(self, poll_timeout_ms: int = 1000):
        while True:
            messages = self.consumer.poll(timeout_ms=poll_timeout_ms)

            for partition_messages in messages.values():
                for message in partition_messages:
                    record = KafkaRecord(
                        value=message.value,
                        topic=message.topic,
                        partition=message.partition,
                        offset=message.offset,
                    )

                    builder = self._get_batch_builder(
                        record.topic,
                        record.partition,
                    )

                    for records in builder.add(record):
                        yield self._create_batch(records)

            for builder in self.batch_builders.values():
                if builder.is_timeout_expired():
                    records = builder.flush()
                    if records:
                        yield self._create_batch(records)

    def flush(self, topic: str, partition: int) -> KafkaBatch | None:
        builder = self.batch_builders.get((topic, partition))

        if builder is None:
            return None

        records = builder.flush()

        if not records:
            return None

        return self._create_batch(records)
