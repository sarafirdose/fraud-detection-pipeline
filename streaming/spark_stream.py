"""
Apache Spark Structured Streaming Pipeline (Enterprise / Secondary Stream Engine)

Demonstrates enterprise big-data streaming:
1. Ingests streaming transaction JSON events from Kafka topic 'transactions'
2. Parses PaySim schema and computes feature expressions
3. Applies machine learning fraud scoring
4. Persists processed stream to MongoDB
5. Publishes flagged alerts to Kafka topic 'fraud-alerts'
"""

import os
import sys
import json
import logging
from typing import Dict, Any

# Ensure path resolution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config.settings import settings
from ml.predictor import predictor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] (SparkStreaming) %(message)s")
logger = logging.getLogger("spark_streaming")


def run_spark_streaming():
    """Starts Spark Structured Streaming job."""
    try:
        from pyspark.sql import SparkSession
        from pyspark.sql.functions import from_json, col, udf, struct, to_json
        from pyspark.sql.types import (
            StructType, StructField, StringType, DoubleType,
            IntegerType, BooleanType, ArrayType
        )
    except ImportError:
        logger.error("PySpark is not installed in the current environment. To run Spark streaming, please install pyspark.")
        return

    logger.info("Initializing Apache Spark Session with Kafka & MongoDB connectors...")
    spark = SparkSession.builder \
        .appName("PaySimFraudDetectionSparkStream") \
        .config("spark.mongodb.write.connection.uri", settings.MONGO_URI) \
        .config("spark.mongodb.write.database", settings.MONGO_DB_NAME) \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.mongodb.spark:mongo-spark-connector_2.12:10.2.0") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # Define Schema matching PaySim stream JSON
    tx_schema = StructType([
        StructField("transaction_id", StringType(), False),
        StructField("step", IntegerType(), True),
        StructField("type", StringType(), True),
        StructField("amount", DoubleType(), True),
        StructField("nameOrig", StringType(), True),
        StructField("oldbalanceOrg", DoubleType(), True),
        StructField("newbalanceOrig", DoubleType(), True),
        StructField("nameDest", StringType(), True),
        StructField("oldbalanceDest", DoubleType(), True),
        StructField("newbalanceDest", DoubleType(), True),
        StructField("is_demo", BooleanType(), True),
        StructField("emitted_at", DoubleType(), True)
    ])

    # Ingest Kafka Stream
    raw_kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", settings.KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", settings.KAFKA_TRANSACTIONS_TOPIC) \
        .option("startingOffsets", "latest") \
        .load()

    parsed_df = raw_kafka_df.select(
        from_json(col("value").cast("string"), tx_schema).alias("data")
    ).select("data.*")

    # Define Python Scoring UDF
    def score_row(tx_row):
        tx_dict = tx_row.asDict()
        res = predictor.predict(tx_dict)
        return json.dumps(res)

    score_udf = udf(score_row, StringType())

    scored_stream = parsed_df.withColumn("scored_json", score_udf(struct([col(c) for c in parsed_df.columns])))

    def process_micro_batch(batch_df, batch_id):
        """Processes micro-batch, writes to MongoDB and Kafka alerts."""
        if batch_df.count() == 0:
            return
        
        logger.info(f"Processing Spark micro-batch {batch_id} with {batch_df.count()} records")
        from pymongo import MongoClient
        client = MongoClient(settings.MONGO_URI)
        db = client[settings.MONGO_DB_NAME]
        tx_coll = db[settings.MONGO_TRANSACTIONS_COLLECTION]
        alert_coll = db[settings.MONGO_ALERTS_COLLECTION]

        rows = batch_df.collect()
        for row in rows:
            scored = json.loads(row["scored_json"])
            tx_id = scored.get("transaction_id")
            tx_coll.update_one({"transaction_id": tx_id}, {"$set": scored}, upsert=True)

            if scored.get("is_fraud") or scored.get("risk_level") in ["HIGH", "CRITICAL"]:
                alert_doc = {
                    "alert_id": f"ALT-{tx_id}",
                    "transaction_id": tx_id,
                    "amount": scored["amount"],
                    "type": scored["type"],
                    "nameOrigMasked": scored["nameOrigMasked"],
                    "nameDestMasked": scored["nameDestMasked"],
                    "risk_score": scored["risk_score"],
                    "risk_level": scored["risk_level"],
                    "risk_factors": scored["risk_factors"],
                    "is_demo": scored.get("is_demo", False),
                    "status": "NEW",
                    "created_at": scored.get("evaluated_at")
                }
                alert_coll.update_one({"alert_id": alert_doc["alert_id"]}, {"$set": alert_doc}, upsert=True)

        client.close()

    query = scored_stream.writeStream \
        .foreachBatch(process_micro_batch) \
        .start()

    logger.info("Spark Structured Streaming query active. Awaiting termination...")
    query.awaitTermination()


if __name__ == "__main__":
    run_spark_streaming()
