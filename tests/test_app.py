"""
Tests for the Mergington High School Activities API

Uses pytest with FastAPI TestClient and the AAA (Arrange-Act-Assert) pattern.
Includes a fixture to reset the activities state before each test to ensure isolation.
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

# Create a TestClient for the app
client = TestClient(app)

# Store the original activities to reset between tests
original_activities = None


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state before each test"""
    global original_activities
    if original_activities is None:
        original_activities = copy.deepcopy(activities)

    activities.clear()
    activities.update(copy.deepcopy(original_activities))
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


def test_get_activities_returns_200_and_data():
    """Test that GET /activities returns 200 and contains activity data"""
    # Arrange: state is reset by fixture

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]


def test_signup_adds_participant():
    """Test that signing up for an activity adds the participant"""
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    response = client.get("/activities")
    initial_count = len(response.json()[activity_name]["participants"])

    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"

    response = client.get("/activities")
    assert email in response.json()[activity_name]["participants"]
    assert len(response.json()[activity_name]["participants"]) == initial_count + 1


def test_signup_duplicate_returns_400():
    """Test that signing up twice returns 400 error"""
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # already in sample data

    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_remove_participant_success():
    """Test that removing a participant works"""
    activity_name = "Programming Class"
    email = "emma@mergington.edu"

    response = client.get("/activities")
    assert email in response.json()[activity_name]["participants"]

    response = client.delete(f"/activities/{activity_name}/participants/{email}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from {activity_name}"

    response = client.get("/activities")
    assert email not in response.json()[activity_name]["participants"]


def test_remove_participant_not_found_returns_404():
    """Test that removing a non-existent participant returns 404"""
    activity_name = "Tennis Club"
    email = "nonexistent@mergington.edu"

    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_signup_invalid_activity_returns_404():
    """Test that signing up for non-existent activity returns 404"""
    activity_name = "Nonexistent Activity"
    email = "student@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
