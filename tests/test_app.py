"""
Test suite for the Mergington High School API

Tests cover:
- GET /activities endpoint
- POST /activities/{activity_name}/signup endpoint
- POST /activities/{activity_name}/unregister endpoint
"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # Should have 9 activities
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball Team" in data

    def test_get_activities_contains_activity_details(self, client):
        """Test that activities have required fields"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity

    def test_get_activities_shows_current_participants(self, client):
        """Test that activities show current participants"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestActivitySignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_student_for_activity(self, client):
        """Test that a new student can sign up for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify student was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newstudent@mergington.edu" in activities["Basketball Team"]["participants"]

    def test_signup_fails_for_nonexistent_activity(self, client):
        """Test that signup fails if activity doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_fails_if_already_signed_up(self, client):
        """Test that a student can't sign up twice for the same activity"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_multiple_students_can_signup(self, client):
        """Test that multiple different students can sign up"""
        # Sign up first student
        response1 = client.post(
            "/activities/Art Studio/signup",
            params={"email": "student1@mergington.edu"}
        )
        assert response1.status_code == 200
        
        # Sign up second student
        response2 = client.post(
            "/activities/Art Studio/signup",
            params={"email": "student2@mergington.edu"}
        )
        assert response2.status_code == 200
        
        # Verify both are signed up
        activities_response = client.get("/activities")
        participants = activities_response.json()["Art Studio"]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants

    def test_signup_with_various_activity_names(self, client):
        """Test signup works with different activity names"""
        activities_to_test = [
            "Drama Club",
            "Science Club",
            "Swimming Club"
        ]
        
        for activity in activities_to_test:
            email = f"test_{activity.replace(' ', '_').lower()}@mergington.edu"
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200


class TestActivityUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_student_from_activity(self, client):
        """Test that a student can unregister from an activity"""
        # First, verify the student is signed up
        activities_response = client.get("/activities")
        assert "michael@mergington.edu" in activities_response.json()["Chess Club"]["participants"]
        
        # Unregister
        response = client.post(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify student was removed
        activities_response = client.get("/activities")
        assert "michael@mergington.edu" not in activities_response.json()["Chess Club"]["participants"]

    def test_unregister_fails_for_nonexistent_activity(self, client):
        """Test that unregister fails if activity doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_fails_if_not_signed_up(self, client):
        """Test that unregister fails if student isn't signed up"""
        response = client.post(
            "/activities/Basketball Team/unregister",
            params={"email": "notstudent@mergington.edu"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_then_signup_again(self, client):
        """Test that a student can unregister and then sign up again"""
        activity = "Debate Team"
        email = "testuser@mergington.edu"
        
        # Sign up
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.post(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Sign up again
        response3 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response3.status_code == 200
        
        # Verify student is signed up
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]


class TestActivityDataConsistency:
    """Tests for data consistency and integrity"""
    
    def test_participant_count_accuracy(self, client):
        """Test that participant counts remain accurate after operations"""
        activity = "Swimming Club"
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Sign up new student
        client.post(
            f"/activities/{activity}/signup",
            params={"email": "swimmer1@mergington.edu"}
        )
        
        # Check count increased
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count + 1
        
        # Unregister student
        client.post(
            f"/activities/{activity}/unregister",
            params={"email": "swimmer1@mergington.edu"}
        )
        
        # Check count returned to original
        response = client.get("/activities")
        assert len(response.json()[activity]["participants"]) == initial_count

    def test_different_activities_independent(self, client):
        """Test that changes to one activity don't affect others"""
        email = "student@mergington.edu"
        
        # Sign up for one activity
        client.post(
            "/activities/Drama Club/signup",
            params={"email": email}
        )
        
        # Verify not signed up for another
        activities_response = client.get("/activities")
        assert email not in activities_response.json()["Debate Team"]["participants"]
        assert email in activities_response.json()["Drama Club"]["participants"]
