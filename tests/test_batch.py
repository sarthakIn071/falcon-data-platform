from processing.batch import BatchBuilder


def test_batch_closes_when_batch_size_is_reached():
    builder = BatchBuilder[int](batch_size=3)

    assert builder.add(1) == []
    assert builder.add(2) == []

    batches = builder.add(3)

    assert batches == [[1, 2, 3]]
    assert builder.size() == 0


def test_partial_batch_can_be_flushed():
    builder = BatchBuilder[int](batch_size=3)

    builder.add(1)
    builder.add(2)

    batch = builder.flush()

    assert batch == [1, 2]
    assert builder.size() == 0


def test_multiple_batches():
    builder = BatchBuilder[int](batch_size=2)

    assert builder.add(1) == []
    assert builder.add(2) == [[1, 2]]

    assert builder.add(3) == []
    assert builder.add(4) == [[3, 4]]


def test_invalid_batch_size():
    try:
        BatchBuilder[int](batch_size=0)
        assert False
    except ValueError as exc:
        assert str(exc) == "batch_size must be greater than zero"

def test_timeout_is_not_expired_for_empty_batch():
    builder = BatchBuilder[int](
        batch_size=3,
        timeout_seconds=30,
    )

    assert builder.is_timeout_expired() is False

def test_timeout_is_expired(monkeypatch):
    current_time = 100.0

    monkeypatch.setattr(
        "processing.batch.monotonic",
        lambda: current_time,
    )

    builder = BatchBuilder[int](
        batch_size=3,
        timeout_seconds=30,
    )

    builder.add(1)

    current_time = 129.0

    assert builder.is_timeout_expired() is False

    current_time = 130.0

    assert builder.is_timeout_expired() is True

def test_flush_resets_timeout():
    builder = BatchBuilder[int](
        batch_size=3,
        timeout_seconds=30,
    )

    builder.add(1)

    assert builder.size() == 1

    builder.flush()

    assert builder.size() == 0
    assert builder.is_timeout_expired() is False