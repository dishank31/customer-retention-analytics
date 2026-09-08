"""
Phase 6 — Churn Prediction
============================
Builds 4 ML models (Logistic Regression, Decision Tree, Random Forest, XGBoost)
with temporal train/test split, SMOTE for class imbalance, SHAP explainability,
and comprehensive evaluation.
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    roc_curve, precision_recall_curve, classification_report
)
from imblearn.over_sampling import SMOTE
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

warnings.filterwarnings("ignore", category=UserWarning)

# Try importing xgboost; fall back to GradientBoosting if unavailable
try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("  ⚠ xgboost not installed, using sklearn GradientBoosting instead.")

# Try importing shap
try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False
    print("  ⚠ shap not installed, skipping SHAP analysis.")


# ─── Churn Label Creation ───────────────────────────────────────────────

def create_churn_labels(transactions, analysis_date=config.ANALYSIS_DATE,
                         churn_window=config.CHURN_WINDOW_DAYS):
    """
    Define churn using a temporal observation/prediction split.

    Observation period: all transactions before split_date
    Prediction window:  split_date to analysis_date (90 days)
    Churn = 1 if customer made NO purchase in the prediction window.
    """
    txn = transactions.copy()
    txn["order_date"] = pd.to_datetime(txn["order_date"])

    split_date = pd.Timestamp(config.CHURN_SPLIT_DATE)

    # Customers who purchased at least once in the observation period
    obs_customers = txn[txn["order_date"] < split_date]["customer_id"].unique()

    # Customers who purchased in the prediction window
    pred_window = txn[
        (txn["order_date"] >= split_date) &
        (txn["order_date"] <= pd.Timestamp(analysis_date))
    ]["customer_id"].unique()

    # Churn labels
    churn_labels = pd.DataFrame({
        "customer_id": obs_customers,
        "churn": [0 if cid in pred_window else 1 for cid in obs_customers]
    })

    churn_rate = churn_labels["churn"].mean()
    print(f"  Churn definition: no purchase within {churn_window} days after {split_date.date()}")
    print(f"  Churn rate: {churn_rate:.1%} ({churn_labels['churn'].sum()} / {len(churn_labels)})")

    return churn_labels


# ─── Feature Preparation ────────────────────────────────────────────────

def prepare_features(customer_data, churn_labels):
    """Prepare feature matrix and target for modeling."""

    df = customer_data.merge(churn_labels, on="customer_id", how="inner")

    # Select modeling features
    feature_cols = [
        "recency_days", "frequency", "monetary", "avg_order_value",
        "median_order_value", "purchase_std", "categories_purchased",
        "category_concentration", "avg_quantity", "discount_usage_rate",
        "avg_discount_pct", "return_rate", "interpurchase_time_avg",
        "interpurchase_time_std", "spending_trend", "frequency_trend",
        "aov_trend", "engagement_score", "emails_opened_30d",
        "website_visits_30d", "campaign_clicks_30d", "app_sessions_30d",
        "support_tickets", "customer_tenure_days", "loyalty_program",
        "age",
    ]

    # Only use columns that exist
    available_features = [c for c in feature_cols if c in df.columns]

    X = df[available_features].copy()
    y = df["churn"].copy()

    # Handle any remaining NaN
    X = X.fillna(0)

    # Replace infinities
    X = X.replace([np.inf, -np.inf], 0)

    return X, y, available_features, df


# ─── Model Training ─────────────────────────────────────────────────────

def train_models(X_train, y_train):
    """Train all 4 models and return them."""

    models = {}

    # 1. Logistic Regression
    models["Logistic Regression"] = LogisticRegression(
        max_iter=1000, random_state=config.RANDOM_SEED, class_weight="balanced"
    )

    # 2. Decision Tree
    models["Decision Tree"] = DecisionTreeClassifier(
        max_depth=8, random_state=config.RANDOM_SEED, class_weight="balanced"
    )

    # 3. Random Forest
    models["Random Forest"] = RandomForestClassifier(
        n_estimators=200, max_depth=12, random_state=config.RANDOM_SEED,
        class_weight="balanced", n_jobs=-1
    )

    # 4. XGBoost or GradientBoosting
    if HAS_XGBOOST:
        # Calculate scale_pos_weight for imbalanced data
        n_pos = y_train.sum()
        n_neg = len(y_train) - n_pos
        scale_weight = n_neg / max(n_pos, 1)
        models["XGBoost"] = XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            scale_pos_weight=scale_weight,
            random_state=config.RANDOM_SEED, eval_metric="logloss",
            verbosity=0
        )
    else:
        models["Gradient Boosting"] = GradientBoostingClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            random_state=config.RANDOM_SEED
        )

    # Train all
    for name, model in models.items():
        print(f"  Training {name}...")
        model.fit(X_train, y_train)

    return models


# ─── Evaluation ──────────────────────────────────────────────────────────

def evaluate_models(models, X_test, y_test, feature_names):
    """Evaluate all models and generate comparison plots."""
    results = {}

    fig_roc, ax_roc = plt.subplots(figsize=(10, 7))
    fig_pr, ax_pr = plt.subplots(figsize=(10, 7))
    colors = ["#2ecc71", "#3498db", "#e74c3c", "#9b59b6"]

    for i, (name, model) in enumerate(models.items()):
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        auc_roc = roc_auc_score(y_test, y_prob)
        auc_pr = average_precision_score(y_test, y_prob)

        results[name] = {
            "Accuracy": acc, "Precision": prec, "Recall": rec,
            "F1": f1, "AUC-ROC": auc_roc, "AUC-PR": auc_pr,
        }

        print(f"\n  {name}:")
        print(f"    Accuracy: {acc:.3f}  Precision: {prec:.3f}  "
              f"Recall: {rec:.3f}  F1: {f1:.3f}")
        print(f"    AUC-ROC: {auc_roc:.3f}  AUC-PR: {auc_pr:.3f}")

        # ROC curve
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        ax_roc.plot(fpr, tpr, color=colors[i], linewidth=2,
                     label=f"{name} (AUC={auc_roc:.3f})")

        # PR curve
        precision_vals, recall_vals, _ = precision_recall_curve(y_test, y_prob)
        ax_pr.plot(recall_vals, precision_vals, color=colors[i], linewidth=2,
                    label=f"{name} (AP={auc_pr:.3f})")

        # Confusion matrix
        fig_cm, ax_cm = plt.subplots(figsize=(6, 5))
        cm = confusion_matrix(y_test, y_pred)
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax_cm,
                     xticklabels=["No Churn", "Churn"],
                     yticklabels=["No Churn", "Churn"])
        ax_cm.set_title(f"Confusion Matrix — {name}")
        ax_cm.set_xlabel("Predicted")
        ax_cm.set_ylabel("Actual")
        plt.tight_layout()
        fig_cm.savefig(
            os.path.join(config.OUTPUT_FIGURES, f"confusion_matrix_{name.lower().replace(' ', '_')}.png"),
            dpi=150, bbox_inches="tight"
        )
        plt.close(fig_cm)

    # Finalize ROC plot
    ax_roc.plot([0, 1], [0, 1], "k--", alpha=0.5)
    ax_roc.set_xlabel("False Positive Rate")
    ax_roc.set_ylabel("True Positive Rate")
    ax_roc.set_title("ROC Curve Comparison")
    ax_roc.legend(loc="lower right")
    ax_roc.grid(True, alpha=0.3)
    fig_roc.tight_layout()
    fig_roc.savefig(os.path.join(config.OUTPUT_FIGURES, "roc_comparison.png"),
                     dpi=150, bbox_inches="tight")
    plt.close(fig_roc)

    # Finalize PR plot
    ax_pr.set_xlabel("Recall")
    ax_pr.set_ylabel("Precision")
    ax_pr.set_title("Precision-Recall Curve Comparison")
    ax_pr.legend(loc="upper right")
    ax_pr.grid(True, alpha=0.3)
    fig_pr.tight_layout()
    fig_pr.savefig(os.path.join(config.OUTPUT_FIGURES, "pr_comparison.png"),
                    dpi=150, bbox_inches="tight")
    plt.close(fig_pr)

    return results


def plot_feature_importance(models, feature_names):
    """Plot feature importance for tree-based models."""
    fig, axes = plt.subplots(1, 2, figsize=(18, 8))

    for idx, name in enumerate(["Random Forest",
                                 "XGBoost" if HAS_XGBOOST else "Gradient Boosting"]):
        if name not in models:
            continue
        model = models[name]
        importances = model.feature_importances_
        sorted_idx = np.argsort(importances)[-15:]  # Top 15

        axes[idx].barh(
            [feature_names[i] for i in sorted_idx],
            importances[sorted_idx],
            color=sns.color_palette("viridis", len(sorted_idx))
        )
        axes[idx].set_title(f"Top 15 Features — {name}")
        axes[idx].set_xlabel("Importance")

    plt.tight_layout()
    plt.savefig(os.path.join(config.OUTPUT_FIGURES, "feature_importance.png"),
                dpi=150, bbox_inches="tight")
    plt.close()


def shap_analysis(best_model, X_test, feature_names, model_name):
    """Run SHAP analysis on the best model."""
    if not HAS_SHAP:
        print("  ⚠ Skipping SHAP analysis (shap not installed)")
        return

    print(f"\n  Running SHAP analysis on {model_name}...")

    # Use TreeExplainer for tree-based models
    try:
        explainer = shap.TreeExplainer(best_model)
        shap_values = explainer.shap_values(X_test)
    except Exception:
        try:
            explainer = shap.Explainer(best_model, X_test)
            shap_values = explainer(X_test).values
        except Exception as e:
            print(f"  ⚠ SHAP analysis failed: {e}")
            return

    # Handle multi-output (some models return list)
    if isinstance(shap_values, list):
        shap_values = shap_values[1]  # Class 1 = churn

    # Summary plot
    fig, ax = plt.subplots(figsize=(12, 8))
    shap.summary_plot(shap_values, X_test, feature_names=feature_names,
                       show=False, max_display=15)
    plt.title(f"SHAP Feature Importance — {model_name}")
    plt.tight_layout()
    plt.savefig(os.path.join(config.OUTPUT_FIGURES, "shap_summary.png"),
                dpi=150, bbox_inches="tight")
    plt.close()

    # Bar plot
    fig, ax = plt.subplots(figsize=(10, 7))
    shap.summary_plot(shap_values, X_test, feature_names=feature_names,
                       plot_type="bar", show=False, max_display=15)
    plt.title(f"SHAP Mean Absolute Impact — {model_name}")
    plt.tight_layout()
    plt.savefig(os.path.join(config.OUTPUT_FIGURES, "shap_bar.png"),
                dpi=150, bbox_inches="tight")
    plt.close()

    print("  ✓ SHAP plots saved")


# ─── Main Runner ─────────────────────────────────────────────────────────

def run(customer_data=None, transactions=None):
    """Run the full churn prediction pipeline."""
    print("\n" + "="*60)
    print("PHASE 6: Churn Prediction")
    print("="*60)

    if transactions is None:
        transactions = pd.read_csv(os.path.join(config.DATA_RAW, "transactions.csv"))
    if customer_data is None:
        customer_data = pd.read_csv(
            os.path.join(config.DATA_PROCESSED, "customer_profitable.csv")
        )

    # 1. Create churn labels
    print("\n  Creating churn labels...")
    churn_labels = create_churn_labels(transactions)

    # 2. Prepare features
    print("\n  Preparing features...")
    X, y, feature_names, full_df = prepare_features(customer_data, churn_labels)
    print(f"  Features: {len(feature_names)}, Samples: {len(X)}")

    # 3. Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.TEST_SIZE,
        random_state=config.RANDOM_SEED, stratify=y
    )
    print(f"  Train: {len(X_train)} | Test: {len(X_test)}")
    print(f"  Train churn rate: {y_train.mean():.1%} | Test churn rate: {y_test.mean():.1%}")

    # 4. SMOTE on training data
    print("\n  Applying SMOTE...")
    smote = SMOTE(random_state=config.RANDOM_SEED)
    X_train_sm, y_train_sm = smote.fit_resample(X_train, y_train)
    print(f"  After SMOTE — Train: {len(X_train_sm)} "
          f"(Churn: {y_train_sm.sum()}, No Churn: {(y_train_sm == 0).sum()})")

    # 5. Scale features
    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(scaler.fit_transform(X_train_sm),
                                   columns=feature_names)
    X_test_scaled = pd.DataFrame(scaler.transform(X_test),
                                  columns=feature_names)

    # 6. Train models
    print("\n  Training models...")
    models = train_models(X_train_scaled, y_train_sm)

    # 7. Evaluate
    print("\n  Evaluating models...")
    results = evaluate_models(models, X_test_scaled, y_test, feature_names)

    # Results summary
    results_df = pd.DataFrame(results).T
    print(f"\n  Model Comparison:")
    print(results_df.round(3).to_string())

    # 8. Feature importance
    print("\n  Plotting feature importance...")
    plot_feature_importance(models, feature_names)

    # 9. Select best model (by AUC-ROC)
    best_name = max(results, key=lambda k: results[k]["AUC-ROC"])
    best_model = models[best_name]
    print(f"\n  ★ Best model: {best_name} (AUC-ROC = {results[best_name]['AUC-ROC']:.3f})")

    # 10. SHAP analysis on best model
    shap_analysis(best_model, X_test_scaled, feature_names, best_name)

    # 11. Generate churn probabilities for ALL customers
    print("\n  Generating churn probabilities for all customers...")
    X_all = customer_data[feature_names].fillna(0).replace([np.inf, -np.inf], 0)
    X_all_scaled = pd.DataFrame(scaler.transform(X_all), columns=feature_names)
    churn_probs = best_model.predict_proba(X_all_scaled)[:, 1]

    customer_data["churn_prob"] = churn_probs
    customer_data["churn_predicted"] = (churn_probs >= 0.5).astype(int)

    # Merge actual churn labels for customers that have them
    customer_data = customer_data.merge(
        churn_labels, on="customer_id", how="left"
    )
    customer_data.rename(columns={"churn": "churn_actual"}, inplace=True)

    # 12. Save model and scaler
    joblib.dump(best_model, os.path.join(config.OUTPUT_MODELS, f"best_model_{best_name.lower().replace(' ', '_')}.pkl"))
    joblib.dump(scaler, os.path.join(config.OUTPUT_MODELS, "feature_scaler.pkl"))

    # Save results
    results_df.to_csv(os.path.join(config.OUTPUT_FIGURES, "model_comparison.csv"))

    # Churn probability distribution plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(customer_data["churn_prob"], bins=50, color="#e74c3c",
            edgecolor="white", alpha=0.8)
    ax.axvline(0.5, color="black", linestyle="--", linewidth=1.5, label="Threshold (0.5)")
    ax.set_title("Churn Probability Distribution")
    ax.set_xlabel("Churn Probability")
    ax.set_ylabel("Customer Count")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(config.OUTPUT_FIGURES, "churn_probability_dist.png"),
                dpi=150, bbox_inches="tight")
    plt.close()

    # Save updated customer data
    out_path = os.path.join(config.DATA_PROCESSED, "customer_churn.csv")
    customer_data.to_csv(out_path, index=False)
    print(f"\n  ✓ Churn predictions → {out_path}")
    print(f"  ✓ Model saved → {config.OUTPUT_MODELS}")

    return customer_data, models, best_name, results


if __name__ == "__main__":
    run()
