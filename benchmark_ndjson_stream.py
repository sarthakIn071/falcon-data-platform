
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

config = ParserConfig(
    format="JSON",
    json_mode="LINES",
)

# Generate NDJSON directly into a file.
# Each line contains one independent JSON object.
with tempfile.NamedTemporaryFile(
    mode="w",
    encoding="utf-8",
    suffix=".ndjson",
    delete=False,
) as file:
    file_path = file.name

    for i in range(RECORD_COUNT):
        json.dump(
            {
                "customer_id": i + 1,
                "name": f"Customer {i + 1}",
                "email": f"customer{i + 1}@example.com",
                "city": "Noida",
            },
            file,
        )
        file.write("\n")


try:
    print(f"Generated records: {RECORD_COUNT:,}")
    print(
        f"File size: "
        f"{os.path.getsize(file_path) / (1024 * 1024):.2f} MB"
    )

    count = 0

    rss_before = process.memory_info().rss
    peak_rss = rss_before

    tracemalloc.start()
    start_time = time.perf_counter()

    with open(file_path, "rb") as stream:
        for record in parser.parse_stream(stream, config):
            count += 1

            if count % 10_000 == 0:
                current_rss = process.memory_info().rss
                peak_rss = max(peak_rss, current_rss)

            if count == 1:
                print("First record:", record)

    elapsed = time.perf_counter() - start_time

    rss_after = process.memory_info().rss
    peak_rss = max(peak_rss, rss_after)

    current_memory, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print("\n--- NDJSON Benchmark Results ---")
    print(f"Records processed: {count:,}")
    print(f"Processing time: {elapsed:.2f} seconds")
    print(f"Records per second: {count / elapsed:,.0f}")
    print(f"Peak Python memory: {peak_memory / (1024 * 1024):.2f} MB")
    print(f"RSS before parsing: {rss_before / (1024 * 1024):.2f} MB")
    print(f"Peak RSS during parsing: {peak_rss / (1024 * 1024):.2f} MB")
    print(f"RSS after parsing: {rss_after / (1024 * 1024):.2f} MB")


finally:
    if os.path.exists(file_path):
        os.remove(file_path)
