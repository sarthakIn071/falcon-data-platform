from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("FalconDependencySmokeTest")
    .master("local[2]")
    .getOrCreate()
)

print("Spark version:", spark.version)
print("Test result:", spark.range(5).count())

spark.stop()
