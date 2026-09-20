"""
Customer Retention Analytics — Full Pipeline Runner
=====================================================
Runs all 7 phases sequentially with logging and error handling.
Built on the Olist Brazilian E-Commerce dataset.

Usage:
    python main.py              # Run all phases
    python main.py --phase 3    # Run from Phase 3 onwards
"""

import os
import sys
import time
import argparse
from datetime import datetime

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config


def log_phase(phase_num, phase_name, status="START"):
    """Print formatted phase log."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if status == "START":
        print(f"\n{'─'*60}")
        print(f"[{timestamp}] Phase {phase_num}: {phase_name}")
        print(f"{'─'*60}")
    elif status == "DONE":
        print(f"[{timestamp}] ✓ Phase {phase_num} complete.")
    elif status == "ERROR":
        print(f"[{timestamp}] ✗ Phase {phase_num} FAILED.")


def run_pipeline(start_phase=1):
    """Execute the full pipeline from the specified phase."""

    print("\n" + "═" * 60)
    print("  CUSTOMER RETENTION ANALYTICS PIPELINE")
    print(f"  Dataset: Olist Brazilian E-Commerce")
    print(f"  Analysis Date: {config.ANALYSIS_DATE.date()}")
    print(f"  Churn Window: {config.CHURN_WINDOW_DAYS} days")
    print(f"  Currency: {config.CURRENCY_SYMBOL} ({config.CURRENCY_NAME})")
    print("═" * 60)

    start_time = time.time()
    results = {}

    # ─── Phase 1: Dataset Loading (Olist Real Data) ──────────────────────
    if start_phase <= 1:
        log_phase(1, "Olist Dataset Loading & Transformation")
        try:
            from src import load_olist_data

            customers, transactions, engagement = load_olist_data.run()
            results["customers"] = customers
            results["transactions"] = transactions
            results["engagement"] = engagement
            log_phase(1, "Olist Dataset Loading & Transformation", "DONE")
        except FileNotFoundError as e:
            log_phase(1, "Olist Dataset Loading & Transformation", "ERROR")
            print(f"  Error: {e}")
            print("\n  ACTION REQUIRED: Download Olist dataset from Kaggle:")
            print(
                "  https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce"
            )
            print(f"\n  Extract files to: {config.DATA_OLIST_RAW}")
            print("  Required files:")
            for key in config.OLIST_REQUIRED_FILES:
                print(f"    - {config.OLIST_FILES[key]}")
            raise
        except Exception as e:
            log_phase(1, "Olist Dataset Loading & Transformation", "ERROR")
            print(f"  Error: {e}")
            raise

    # ─── Phase 2: Feature Engineering ────────────────────────────────────
    if start_phase <= 2:
        log_phase(2, "Feature Engineering")
        try:
            from src import feature_engineering

            customer_features = feature_engineering.run(
                customers=results.get("customers"),
                transactions=results.get("transactions"),
                engagement=results.get("engagement"),
            )
            results["customer_features"] = customer_features
            log_phase(2, "Feature Engineering", "DONE")
        except Exception as e:
            log_phase(2, "Feature Engineering", "ERROR")
            print(f"  Error: {e}")
            raise

    # ─── Phase 3: Segmentation ───────────────────────────────────────────
    if start_phase <= 3:
        log_phase(3, "Customer Segmentation")
        try:
            from src import segmentation

            segmented = segmentation.run(
                customer_features=results.get("customer_features"),
            )
            results["segmented"] = segmented
            log_phase(3, "Customer Segmentation", "DONE")
        except Exception as e:
            log_phase(3, "Customer Segmentation", "ERROR")
            print(f"  Error: {e}")
            raise

    # ─── Phase 4: Profitability ──────────────────────────────────────────
    if start_phase <= 4:
        log_phase(4, "Customer Profitability")
        try:
            from src import profitability

            profitable = profitability.run(
                segmented_customers=results.get("segmented"),
                transactions=results.get("transactions"),
                customers=results.get("customers"),
                engagement=results.get("engagement"),
            )
            results["profitable"] = profitable
            log_phase(4, "Customer Profitability", "DONE")
        except Exception as e:
            log_phase(4, "Customer Profitability", "ERROR")
            print(f"  Error: {e}")
            raise

    # ─── Phase 5: Churn Prediction ───────────────────────────────────────
    if start_phase <= 5:
        log_phase(5, "Churn Prediction")
        try:
            from src import churn_model

            churn_data, models, best_model_name, model_results = churn_model.run(
                customer_data=results.get("profitable"),
                transactions=results.get("transactions"),
            )
            results["churn_data"] = churn_data
            results["models"] = models
            results["best_model"] = best_model_name
            log_phase(5, "Churn Prediction", "DONE")
        except Exception as e:
            log_phase(5, "Churn Prediction", "ERROR")
            print(f"  Error: {e}")
            raise

    # ─── Phase 6: Retention Prioritization ───────────────────────────────
    if start_phase <= 6:
        log_phase(6, "Retention Prioritization")
        try:
            from src import retention_priority

            final_data = retention_priority.run(
                customer_data=results.get("churn_data"),
            )
            results["final_data"] = final_data
            log_phase(6, "Retention Prioritization", "DONE")
        except Exception as e:
            log_phase(6, "Retention Prioritization", "ERROR")
            print(f"  Error: {e}")
            raise

    # ─── Phase 7: Power BI Export ────────────────────────────────────────
    if start_phase <= 7:
        log_phase(7, "Power BI Export")
        try:
            from src import export_powerbi

            export_powerbi.run(
                final_data=results.get("final_data"),
                transactions=results.get("transactions"),
            )
            log_phase(7, "Power BI Export", "DONE")
        except Exception as e:
            log_phase(7, "Power BI Export", "ERROR")
            print(f"  Error: {e}")
            raise

    # ─── Pipeline Complete ───────────────────────────────────────────────
    elapsed = time.time() - start_time
    print("\n" + "═" * 60)
    print(f"  ✓ PIPELINE COMPLETE — {elapsed:.1f}s")
    print(f"  Output directory: {config.PROJECT_ROOT}")
    print("═" * 60)

    # Summary of outputs
    print("\n  Generated Outputs:")
    print(
        f"    data/raw/         → Olist transformed datasets (customers, transactions, engagement)"
    )
    print(f"    data/processed/   → Processed datasets with engineered features")
    print(f"    outputs/figures/  → Charts & visualizations")
    print(f"    outputs/models/   → Trained ML model + scaler")
    print(f"    outputs/powerbi/  → Power BI-ready CSVs")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Customer Retention Analytics Pipeline (Olist E-Commerce)"
    )
    parser.add_argument(
        "--phase",
        type=int,
        default=1,
        help="Start from this phase (1-7, default: 1)",
    )
    args = parser.parse_args()

    run_pipeline(start_phase=args.phase)
