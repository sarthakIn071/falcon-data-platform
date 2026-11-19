
import json
import time
import tracemalloc
import tempfile
import os
import psutil

from parsers.json_parser import JSONParser
from parsers.models import ParserConfig


RECORD_COUNT = 10_000_000
process = psutil.Process(os.getpid())
parser = JSONParser()
config = ParserConfig(format="JSON")

# Generate a JSON array directly into a file.
# Avoid building the entire dataset in memory.
with tempfile.NamedTemporaryFile(
    mode="w",
    encoding="utf-8",
    suffix=".json",
    delete=False,
) as file:
    file_path = file.name

    file.write("[")

    for i in range(RECORD_COUNT):
        if i > 0:
            file.write(",")

        json.dump(
            {
                "customer_id": i + 1,
                "name": f"Customer {i + 1}",
                "email": f"customer{i + 1}@example.com",
                "city": "Noida",
            },
            file,
        )

    file.write("]")


try:
    print(f"Generated records: {RECORD_COUNT:,}")
    print(f"File size: {os.path.getsize(file_path) / (1024 * 1024):.2f} MB")

    count = 0

    # Memory before parsing
    rss_before = process.memory_info().rss

    # Track peak RSS during parsing
    peak_rss = rss_before

    tracemalloc.start()
    start_time = time.perf_counter()

    with open(file_path, "rb") as stream:
        for record in parser.parse_stream(stream, config):
            count += 1

            # Sample process memory every 10,000 records
            if count % 10_000 == 0:
                current_rss = process.memory_info().rss
                peak_rss = max(peak_rss, current_rss)

            if count == 1:
                print("First record:", record)

    elapsed = time.perf_counter() - start_time

    # Final memory measurement
    rss_after = process.memory_info().rss
    peak_rss = max(peak_rss, rss_after)

    current_memory, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print("\n--- Benchmark Results ---")
    print(f"Records processed: {count:,}")
    print(f"Processing time: {elapsed:.2f} seconds")
    print(f"Records per second: {count / elapsed:,.0f}")
    print(f"Peak Python memory: {peak_memory / (1024 * 1024):.2f} MB")
    print(f"RSS before parsing: {rss_before / (1024 * 1024):.2f} MB")
    print(f"Peak RSS during parsing: {peak_rss / (1024 * 1024):.2f} MB")
    print(f"RSS after parsing: {rss_after / (1024 * 1024):.2f} MB")

finally:
    os.remove(file_path)
