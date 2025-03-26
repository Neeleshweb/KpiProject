import json
from datetime import datetime, timedelta

# File paths
ISSUE_HISTORY_FILE = "issue_history.json"
DASHBOARD_DATA_FILE = "dashboard_data.json"

# Load issue history from file
def load_issue_history(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        exit()

# Save processed dashboard data to file
def save_dashboard_data(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Dashboard data saved to {file_path}")

# Process issue history to calculate daily trends and metrics
def process_issue_history(issue_history):
    sorted_dates = sorted(issue_history.keys(), key=lambda x: datetime.strptime(x, "%Y-%m-%d"))
    trends = {"done": [], "in_progress": [], "to_do": []}

    for i, date in enumerate(sorted_dates):
        day_data = issue_history[date]

        # Append data to trends
        trends["done"].append({"date": date, "value": day_data["done"]})
        trends["in_progress"].append({"date": date, "value": day_data["in_progress"]})
        trends["to_do"].append({"date": date, "value": day_data["to_do"]})

    # Calculate daily deltas for each category
    deltas = {"done": [], "in_progress": [], "to_do": []}
    for category in ["done", "in_progress", "to_do"]:
        for j in range(1, len(trends[category])):
            previous_value = trends[category][j - 1]["value"]
            current_value = trends[category][j]["value"]
            delta = current_value - previous_value
            deltas[category].append({"date": trends[category][j]["date"], "delta": delta})

    return {"trends": trends, "deltas": deltas}

# Main execution
if __name__ == "__main__":
    print("Loading issue history data...")
    issue_history = load_issue_history(ISSUE_HISTORY_FILE)

    print("Calculating daily trends...")
    dashboard_data = process_issue_history(issue_history)

    print("Saving dashboard data...")
    save_dashboard_data(DASHBOARD_DATA_FILE, dashboard_data)

    print("Data preparation complete.")
