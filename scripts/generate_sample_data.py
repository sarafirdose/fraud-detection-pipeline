"""
PaySim-Compatible Synthetic Demo Data Generator

Generates a realistic, highly authentic dataset matching the exact schema and fraud dynamics
of the PaySim mobile-money benchmark dataset.

Schema:
- step: int (hour of simulation, 1 to 744)
- type: str (PAYMENT, TRANSFER, CASH_OUT, DEBIT, CASH_IN)
- amount: float
- nameOrig: str (e.g. C1234567890)
- oldbalanceOrg: float
- newbalanceOrig: float
- nameDest: str (e.g. M1234567890 or C9876543210)
- oldbalanceDest: float
- newbalanceDest: float
- isFraud: int (0 or 1)
- isFlaggedFraud: int (0 or 1)

DISCLAIMER:
This script creates PaySim-compatible synthetic demo data for rapid local testing
and evaluation without needing to download the 500MB+ raw PaySim CSV.
"""

import os
import random
import argparse
import pandas as pd
import numpy as np


def generate_paysim_sample(
    num_records: int = 25000,
    fraud_rate: float = 0.015,
    output_path: str = "data/sample_transactions.csv",
    seed: int = 42
) -> pd.DataFrame:
    """Generate PaySim-compatible synthetic dataset."""
    random.seed(seed)
    np.random.seed(seed)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    types = ["PAYMENT", "CASH_OUT", "CASH_IN", "TRANSFER", "DEBIT"]
    type_weights = [0.35, 0.30, 0.20, 0.12, 0.03]

    records = []
    num_fraud = int(num_records * fraud_rate)
    num_normal = num_records - num_fraud

    print(f"Generating {num_records} PaySim-compatible synthetic records ({num_fraud} fraud, {num_normal} normal)...")

    # 1. Generate Normal Transactions
    for i in range(num_normal):
        step = random.randint(1, 100)
        tx_type = random.choices(types, weights=type_weights)[0]
        orig_id = f"C{random.randint(1000000000, 9999999999)}"

        if tx_type == "PAYMENT":
            dest_id = f"M{random.randint(1000000000, 9999999999)}"
            amount = round(random.expovariate(1 / 3000.0) + 5.0, 2)
            oldbalance_org = round(random.uniform(amount * 0.5, amount * 5.0) + 100, 2)
            newbalance_orig = max(0.0, round(oldbalance_org - amount, 2))
            oldbalance_dest = 0.0  # PaySim standard for merchant payments
            newbalance_dest = 0.0
        elif tx_type == "CASH_IN":
            dest_id = f"C{random.randint(1000000000, 9999999999)}"
            amount = round(random.expovariate(1 / 15000.0) + 50.0, 2)
            oldbalance_org = round(random.uniform(100, 50000), 2)
            newbalance_orig = round(oldbalance_org + amount, 2)
            oldbalance_dest = round(random.uniform(500, 100000), 2)
            newbalance_dest = round(oldbalance_dest - amount if oldbalance_dest >= amount else 0.0, 2)
        elif tx_type == "DEBIT":
            dest_id = f"C{random.randint(1000000000, 9999999999)}"
            amount = round(random.expovariate(1 / 2000.0) + 10.0, 2)
            oldbalance_org = round(random.uniform(amount, amount * 10.0), 2)
            newbalance_orig = round(oldbalance_org - amount, 2)
            oldbalance_dest = round(random.uniform(100, 50000), 2)
            newbalance_dest = round(oldbalance_dest + amount, 2)
        elif tx_type == "TRANSFER":
            dest_id = f"C{random.randint(1000000000, 9999999999)}"
            amount = round(random.expovariate(1 / 25000.0) + 100.0, 2)
            oldbalance_org = round(random.uniform(amount * 1.1, amount * 3.0), 2)
            newbalance_orig = round(oldbalance_org - amount, 2)
            oldbalance_dest = round(random.uniform(100, 50000), 2)
            newbalance_dest = round(oldbalance_dest + amount, 2)
        else:  # CASH_OUT
            dest_id = f"C{random.randint(1000000000, 9999999999)}"
            amount = round(random.expovariate(1 / 18000.0) + 50.0, 2)
            oldbalance_org = round(random.uniform(amount * 1.05, amount * 2.5), 2)
            newbalance_orig = round(oldbalance_org - amount, 2)
            oldbalance_dest = round(random.uniform(0, 50000), 2)
            newbalance_dest = round(oldbalance_dest + amount, 2)

        records.append({
            "step": step,
            "type": tx_type,
            "amount": amount,
            "nameOrig": orig_id,
            "oldbalanceOrg": oldbalance_org,
            "newbalanceOrig": newbalance_orig,
            "nameDest": dest_id,
            "oldbalanceDest": oldbalance_dest,
            "newbalanceDest": newbalance_dest,
            "isFraud": 0,
            "isFlaggedFraud": 0
        })

    # 2. Generate Fraud Transactions (PaySim authentic patterns: TRANSFER & CASH_OUT account drain)
    for i in range(num_fraud):
        step = random.randint(1, 100)
        # In PaySim, fraudulent actions are exclusively TRANSFER and CASH_OUT
        tx_type = random.choice(["TRANSFER", "CASH_OUT"])
        orig_id = f"C{random.randint(1000000000, 9999999999)}"
        dest_id = f"C{random.randint(1000000000, 9999999999)}"

        # Fraud pattern 1: Account drain (emptying the account entirely)
        amount = round(random.uniform(50000.0, 1500000.0), 2)
        oldbalance_org = amount  # Drain complete balance
        newbalance_orig = 0.0    # Emptied to zero!

        # Fraud destination dynamics
        if random.random() < 0.4:
            # Anomaly: destination balance is 0 before and 0 after (cash swept immediately)
            oldbalance_dest = 0.0
            newbalance_dest = 0.0
        else:
            oldbalance_dest = round(random.uniform(0.0, 50000.0), 2)
            # In some fraud cases, destination balance increases abnormally or has discrepancy
            newbalance_dest = round(oldbalance_dest + amount, 2)

        is_flagged = 1 if amount > 200000.0 and random.random() < 0.2 else 0

        records.append({
            "step": step,
            "type": tx_type,
            "amount": amount,
            "nameOrig": orig_id,
            "oldbalanceOrg": oldbalance_org,
            "newbalanceOrig": newbalance_orig,
            "nameDest": dest_id,
            "oldbalanceDest": oldbalance_dest,
            "newbalanceDest": newbalance_dest,
            "isFraud": 1,
            "isFlaggedFraud": is_flagged
        })

    # Shuffle dataset
    random.shuffle(records)

    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"Successfully generated PaySim-compatible synthetic demo data: {output_path}")
    print(f"Total Rows: {len(df)} | Fraud Count: {df['isFraud'].sum()} ({df['isFraud'].mean()*100:.2f}%)")
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate PaySim-compatible synthetic demo dataset")
    parser.add_argument("--rows", type=int, default=30000, help="Number of records to generate")
    parser.add_argument("--fraud-rate", type=float, default=0.015, help="Fraud proportion (e.g. 0.015 for 1.5%)")
    parser.add_argument("--output", type=str, default="data/sample_transactions.csv", help="Output CSV path")
    args = parser.parse_args()

    generate_paysim_sample(
        num_records=args.rows,
        fraud_rate=args.fraud_rate,
        output_path=args.output
    )
