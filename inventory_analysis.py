"""
Supply Chain Inventory Analysis Script
Yokohama India Pvt. Ltd. - Raw Material Planning
Author: Bhushan Ingale
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ─────────────────────────────────────────────
# STEP 1: Load the CSV
# ─────────────────────────────────────────────
# In Google Colab, upload your file first using:
#   from google.colab import files
#   uploaded = files.upload()
# Then the filename will be available in the current directory.

# If running in Colab, uncomment these 2 lines:
# from google.colab import files
# uploaded = files.upload()

df = pd.read_csv("inventory_data.csv")

print("=" * 55)
print("  SUPPLY CHAIN INVENTORY ANALYSIS REPORT")
print("  Yokohama India Pvt. Ltd. - Raw Material Planning")
print("=" * 55)
print(f"\n  Total records loaded: {len(df)} materials\n")

# ─────────────────────────────────────────────
# STEP 2: Flag each material as Critical / Low / OK
# Logic:
#   Closing Stock < Safety Stock  → Critical
#   Closing Stock < Reorder Point → Low
#   Otherwise                     → OK
# ─────────────────────────────────────────────
def classify_status(row):
    if row["Closing_Stock_kg"] < row["Safety_Stock_kg"]:
        return "Critical"
    elif row["Closing_Stock_kg"] < row["Reorder_Point_kg"]:
        return "Low"
    else:
        return "OK"

df["Stock_Status"] = df.apply(classify_status, axis=1)

# ─────────────────────────────────────────────
# STEP 3: Calculate Days of Stock Remaining
# Formula: Closing_Stock / (Consumed_kg / 30)
# This tells us how many days until stock runs out
# based on the current monthly consumption rate.
# ─────────────────────────────────────────────
df["Days_of_Stock_Remaining"] = (
    df["Closing_Stock_kg"] / (df["Consumed_kg"] / 30)
).round(1)

# Handle edge case: if Consumed_kg is 0, avoid division by zero
df["Days_of_Stock_Remaining"] = df["Days_of_Stock_Remaining"].replace(
    [float("inf"), float("-inf")], 999
).fillna(999)

# ─────────────────────────────────────────────
# STEP 4: Print Summary Report
# ─────────────────────────────────────────────
status_counts = df["Stock_Status"].value_counts()
total = len(df)

print("  ── STOCK STATUS SUMMARY ──────────────────────")
for status in ["Critical", "Low", "OK"]:
    count = status_counts.get(status, 0)
    pct = round((count / total) * 100, 1)
    bar = "█" * int(pct / 4)
    print(f"  {status:<10} {count:>3} materials  ({pct:>5}%)  {bar}")

print(f"\n  Total materials tracked: {total}")
print(f"  Materials needing action (Critical + Low): "
      f"{status_counts.get('Critical', 0) + status_counts.get('Low', 0)}")

# Category breakdown
print("\n  ── BY CATEGORY ───────────────────────────────")
cat_summary = df.groupby("Category")["Stock_Status"].value_counts().unstack(fill_value=0)
print(cat_summary.to_string())

# Top 5 most urgent (lowest days remaining, Critical only)
print("\n  ── TOP 5 MOST URGENT MATERIALS ───────────────")
critical_df = df[df["Stock_Status"] == "Critical"].sort_values("Days_of_Stock_Remaining")
cols = ["Material_ID", "Material_Name", "Closing_Stock_kg",
        "Safety_Stock_kg", "Days_of_Stock_Remaining", "Supplier_Name"]
print(critical_df[cols].head(5).to_string(index=False))

print("\n" + "=" * 55)

# ─────────────────────────────────────────────
# STEP 5: Export filtered CSV (Critical + Low only)
# This is the "action list" — materials that need
# immediate procurement or escalation.
# ─────────────────────────────────────────────
action_df = df[df["Stock_Status"].isin(["Critical", "Low"])].copy()
action_df = action_df.sort_values(["Stock_Status", "Days_of_Stock_Remaining"])

action_df.to_csv("critical_low_materials.csv", index=False)
print(f"\n  Exported {len(action_df)} materials to: critical_low_materials.csv")

# ─────────────────────────────────────────────
# STEP 6: Bar Chart — Closing Stock vs Reorder Point
# ─────────────────────────────────────────────

# Aggregate by category for the chart
chart_data = df.groupby("Category").agg(
    Closing_Stock=("Closing_Stock_kg", "sum"),
    Reorder_Point=("Reorder_Point_kg", "sum")
).reset_index()

categories = chart_data["Category"]
x = range(len(categories))
bar_width = 0.38

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.patch.set_facecolor("#F8F9FA")

# ── Chart 1: Closing Stock vs Reorder Point by Category ──
ax1 = axes[0]
ax1.set_facecolor("#FFFFFF")

bars1 = ax1.bar([i - bar_width/2 for i in x], chart_data["Closing_Stock"],
                width=bar_width, color="#1A4E8C", label="Closing Stock (kg)", zorder=3)
bars2 = ax1.bar([i + bar_width/2 for i in x], chart_data["Reorder_Point"],
                width=bar_width, color="#E05C2A", label="Reorder Point (kg)", zorder=3)

ax1.set_xticks(list(x))
ax1.set_xticklabels(categories, rotation=12, ha="right", fontsize=10)
ax1.set_ylabel("Stock (kg)", fontsize=11)
ax1.set_title("Closing Stock vs Reorder Point\nby Material Category",
              fontsize=13, fontweight="bold", pad=12)
ax1.legend(fontsize=10)
ax1.yaxis.grid(True, linestyle="--", alpha=0.5, zorder=0)
ax1.set_axisbelow(True)

# Add value labels on bars
for bar in bars1:
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1500,
             f'{int(bar.get_height()/1000)}k', ha='center', va='bottom',
             fontsize=8, color="#1A4E8C", fontweight="bold")
for bar in bars2:
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1500,
             f'{int(bar.get_height()/1000)}k', ha='center', va='bottom',
             fontsize=8, color="#E05C2A", fontweight="bold")

# ── Chart 2: Stock Status Distribution (Donut) ──
ax2 = axes[1]
ax2.set_facecolor("#FFFFFF")

status_data = df["Stock_Status"].value_counts()
colors = {"Critical": "#D32F2F", "Low": "#F9A825", "OK": "#388E3C"}
pie_colors = [colors.get(s, "#999") for s in status_data.index]

wedges, texts, autotexts = ax2.pie(
    status_data.values,
    labels=None,
    colors=pie_colors,
    autopct="%1.0f%%",
    startangle=90,
    pctdistance=0.75,
    wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2)
)

for t in autotexts:
    t.set_fontsize(13)
    t.set_fontweight("bold")
    t.set_color("white")

legend_patches = [
    mpatches.Patch(color=colors[s], label=f"{s}  ({status_data.get(s, 0)} materials)")
    for s in ["Critical", "Low", "OK"] if s in status_data
]
ax2.legend(handles=legend_patches, loc="lower center",
           bbox_to_anchor=(0.5, -0.12), fontsize=11, frameon=False)

ax2.set_title("Inventory Health Overview\n(Stock Status Distribution)",
              fontsize=13, fontweight="bold", pad=12)
ax2.text(0, 0, f"{total}\nMaterials", ha="center", va="center",
         fontsize=12, fontweight="bold", color="#333333")

plt.suptitle("Supply Chain Inventory Dashboard — Raw Material Planning",
             fontsize=15, fontweight="bold", y=1.01, color="#1A4E8C")

plt.tight_layout()
plt.savefig("inventory_analysis_chart.png", dpi=150, bbox_inches="tight",
            facecolor="#F8F9FA")
plt.show()

print("\n  Chart saved as: inventory_analysis_chart.png")
print("\n  Script complete. Files generated:")
print("   - critical_low_materials.csv  (action list for procurement)")
print("   - inventory_analysis_chart.png  (dashboard charts)")
print("=" * 55)
