import requests
from datetime import datetime
from datetime import timedelta
import json
import os

# JIRA Configuration
JIRA_BASE_URL = "https://prospects.atlassian.net"
API_TOKEN = "hayetehdhd"  # Replace with your API token
EMAIL = "neelsingh@corelogic.com"

# Authentication
AUTH = (EMAIL, API_TOKEN)

# Function to fetch all boards
def get_boards():
    url = f"{JIRA_BASE_URL}/rest/agile/1.0/board"
    response = requests.get(url, auth=AUTH)
    response.raise_for_status()
    return response.json().get("values", [])

# Function to fetch all sprints for a board (handles pagination)
def get_all_sprints(board_id):
    all_sprints = []
    start_at = 0
    max_results = 50  # Default JIRA page size

    while True:
        url = f"{JIRA_BASE_URL}/rest/agile/1.0/board/{board_id}/sprint?startAt={start_at}&maxResults={max_results}"
        response = requests.get(url, auth=AUTH)
        response.raise_for_status()

        data = response.json()
        sprints = data.get("values", [])
        all_sprints.extend(sprints)

        if len(sprints) < max_results:  # No more pages
            break

        start_at += max_results

    return all_sprints

# Function to find the active sprint from all sprints
def get_active_sprint(all_sprints):
    for sprint in all_sprints:
        if sprint["state"] == "active":
            return sprint
    print("No active sprint found.")
    return None

# Function to fetch sprint details
def get_sprint_details(sprint_id):
    url = f"{JIRA_BASE_URL}/rest/agile/1.0/sprint/{sprint_id}"
    response = requests.get(url, auth=AUTH)
    response.raise_for_status()
    return response.json()

# Function to fetch issues for a sprint
def get_sprint_issues(board_id, sprint_id):
    issues = []
    start_at = 0
    max_results = 50

    while True:
        url = f"{JIRA_BASE_URL}/rest/agile/1.0/board/{board_id}/sprint/{sprint_id}/issue?startAt={start_at}&maxResults={max_results}"
        response = requests.get(url, auth=AUTH)
        response.raise_for_status()
        data = response.json()

        issues.extend(data.get("issues", []))
        if len(data.get("issues", [])) < max_results:  # No more pages
            break
        start_at += max_results

    return issues


# Function to update issue history
def update_issue_history(file_path, done_issues, in_progress_issues, to_do_issues):
    today = datetime.now().strftime("%Y-%m-%d")  # Get today's date as a string

    # Check if the file exists; if not, create it with an empty JSON object
    if not os.path.exists(file_path):
        with open(file_path, "w") as file:
            json.dump({}, file)

    # Load the existing data
    with open(file_path, "r") as file:
        history = json.load(file)

    # Update today's data
    history[today] = {
        "done": done_issues,
        "in_progress": in_progress_issues,
        "to_do": to_do_issues
    }

    # Save the updated data back to the file
    with open(file_path, "w") as file:
        json.dump(history, file, indent=4)

def calculate_working_days_exclusive(start_date, end_date):
    current_date = start_date + timedelta(days=1)  # Start counting from the next day
    working_days = 0

    while current_date < end_date:  # Exclude the end date itself
        if current_date.weekday() < 5:  # 0-4 are weekdays (Monday-Friday)
            working_days += 1
        current_date += timedelta(days=1)

    return working_days


# Function to calculate sprint health
def calculate_sprint_health(sprint_data, issues, history_file_path):
    start_date = datetime.strptime(sprint_data["startDate"], "%Y-%m-%dT%H:%M:%S.%fZ")
    end_date = datetime.strptime(sprint_data["endDate"], "%Y-%m-%dT%H:%M:%S.%fZ")
    today = datetime.now()
    adjusted_end_date = end_date - timedelta(days=1) if end_date.weekday() == 0 else end_date

    # Calculate working days
    total_days = calculate_working_days_exclusive(start_date, adjusted_end_date)
    days_left = calculate_working_days_exclusive(today, adjusted_end_date)

    # Categorize issues dynamically
    total_issues = len(issues)
    done_issues = sum(1 for issue in issues if issue["fields"]["status"]["name"] == "Done")
    in_progress_statuses = {"In Progress", "In Development", "In QA", "On-Hold", "In Code Review", "Pending QA", "Pending Release"}
    in_progress_issues = sum(1 for issue in issues if issue["fields"]["status"]["name"] in in_progress_statuses)
    to_do_issues = total_issues - done_issues - in_progress_issues

    # Update issue history
    update_issue_history(history_file_path, done_issues, in_progress_issues, to_do_issues)

    # Load historical data for analysis
    with open(history_file_path, "r") as file:
        issue_history = json.load(file)

    # Analyze trends for health determination
    dates = sorted(issue_history.keys())
    if len(dates) > 1:  # Need at least two days of data
        prev_day = dates[-2]
        current_day = dates[-1]

        prev_data = issue_history[prev_day]
        current_data = issue_history[current_day]

        done_increase_rate = current_data["done"] - prev_data["done"]
        in_progress_change_rate = current_data["in_progress"] - prev_data["in_progress"]
        to_do_change_rate = prev_data["to_do"] - current_data["to_do"]

        # Define thresholds for health determination
        if done_increase_rate > 2 and in_progress_change_rate < 1 and to_do_change_rate > 2:
            health = "Good"
        elif done_increase_rate <= 1 or to_do_change_rate < 1:
            health = "Bad"
        else:
            health = "Average"
    else:
        health = "Average"  # Default health when no trend data exists

    return {
        "total_days": total_days,
        "days_left": days_left,
        "total_issues": total_issues,
        "done_issues": done_issues,
        "in_progress_issues": in_progress_issues,
        "to_do_issues": to_do_issues,
        "health": health,
    }

# Main Execution
if __name__ == "__main__":
    try:
        # Fetch all boards and find the relevant board
        boards = get_boards()
        board_id = next((b["id"] for b in boards if b["name"] == "All Mobile"), None)
        if not board_id:
            print("Error: Board not found. Exiting.")
            exit()

        # Fetch all sprints for the board
        all_sprints = get_all_sprints(board_id)
        print(f"Fetched {len(all_sprints)} sprints.")

        # Find the active sprint
        active_sprint = get_active_sprint(all_sprints)
        if not active_sprint:
            print("Error: No active sprint found. Exiting.")
            exit()

        sprint_id = active_sprint["id"]
        print(f"Active Sprint ID: {sprint_id}, Name: {active_sprint['name']}")

        # Fetch sprint details and issues
        sprint_data = get_sprint_details(sprint_id)
        issues_data = get_sprint_issues(board_id, sprint_id)

        # Calculate sprint health
        history_file = "issue_history.json"
        sprint_health = calculate_sprint_health(sprint_data, issues_data, history_file)

        print(f"Sprint Health: {sprint_health['health']}")
        print(f"Details: {sprint_health}")

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
