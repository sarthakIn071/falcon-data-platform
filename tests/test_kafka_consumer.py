
from unittest.mock import MagicMock, patch

from kafka import TopicPartition
from kafka.structs import OffsetAndMetadata

from messaging.consumer import FalconKafkaConsumer


@patch("messaging.consumer.KafkaConsumer")
def test_commit_batch(mock_kafka_consumer):
    mock_instance = MagicMock()
    mock_kafka_consumer.return_value = mock_instance

    consumer = FalconKafkaConsumer(
        topic="falcon.raw.customer",
        group_id="falcon-dq",
    )

    consumer.commit_batch(
        topic="falcon.raw.customer",
        partition=0,
        last_offset=102,
    )

    topic_partition = TopicPartition(
        "falcon.raw.customer",
        0,
    )

    mock_instance.commit.assert_called_once_with(
        offsets={
            topic_partition: OffsetAndMetadata(
                offset=103,
                metadata="",
                leader_epoch=-1,
            ),
        }
    )


def test_poll():
    mock_consumer = MagicMock()

    with patch(
        "messaging.consumer.KafkaConsumer",
        return_value=mock_consumer,
    ):
        consumer = FalconKafkaConsumer(
            topic="falcon.raw.customer",
            group_id="test-group",
        )

        consumer.poll(timeout_ms=1000)

        mock_consumer.poll.assert_called_once_with(
            timeout_ms=1000
        )
