import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client():
    return TestClient(app_module.app)


@pytest.fixture(autouse=True)
def restore_activity_state():
    original_state = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(original_state))


def test_get_activities_returns_activity_list(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert isinstance(activities, dict)
    assert expected_activity in activities
    assert "description" in activities[expected_activity]
    assert "participants" in activities[expected_activity]


def test_signup_for_activity_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    participant_email = "newstudent@mergington.edu"
    encoded_activity = quote(activity_name, safe="")

    # Act
    response = client.post(f"/activities/{encoded_activity}/signup?email={participant_email}")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["message"] == f"Signed up {participant_email} for {activity_name}"
    assert participant_email in app_module.activities[activity_name]["participants"]


def test_signup_for_activity_rejects_duplicate_signup(client):
    # Arrange
    activity_name = "Chess Club"
    duplicate_email = "michael@mergington.edu"
    encoded_activity = quote(activity_name, safe="")

    # Act
    response = client.post(f"/activities/{encoded_activity}/signup?email={duplicate_email}")

    # Assert
    assert response.status_code == 400
    response_data = response.json()
    assert response_data["detail"] == "Student already signed up for this activity"


def test_remove_participant_unregisters_student(client):
    # Arrange
    activity_name = "Chess Club"
    participant_email = "michael@mergington.edu"
    encoded_activity = quote(activity_name, safe="")

    # Act
    response = client.delete(f"/activities/{encoded_activity}/participants?email={participant_email}")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["message"] == f"Removed {participant_email} from {activity_name}"
    assert participant_email not in app_module.activities[activity_name]["participants"]


def test_remove_participant_returns_404_for_missing_participant(client):
    # Arrange
    activity_name = "Chess Club"
    missing_email = "missingstudent@mergington.edu"
    encoded_activity = quote(activity_name, safe="")

    # Act
    response = client.delete(f"/activities/{encoded_activity}/participants?email={missing_email}")

    # Assert
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"] == "Participant not found in this activity"
