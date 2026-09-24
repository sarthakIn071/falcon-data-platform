from messaging.event import FalconEvent, SourceInfo
from messaging.producer import FalconKafkaProducer



event = FalconEvent(
    event_id="event-001",
    run_id="run-001",
    source=SourceInfo(
        type="REST_API",
        connector="demo_connector",
        system="demo",
    ),
    entity="customer",
    operation="UPSERT",
    payload={
        "customer_id" : 1001,
        "name" : "John",
        "email" : "john@example.com",
    },
)

producer = FalconKafkaProducer()

result = producer.publish(
    topic="falcon.raw.customer",
    event=event,
    key="1001",
)

print(result)

producer.close()