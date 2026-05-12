import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
import uuid

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from src.main import app
from src.db.session import Base, get_db
from src.models.user import User, UserSession
from src.models.team import Team, TeamMember
from src.core.security import get_password_hash

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user(setup_database):
    db = TestingSessionLocal()
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=email,
        password_hash=get_password_hash("password123"),
        nickname="Test User",
        status=1
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()
    db.close()

@pytest.fixture
def test_team(test_user):
    db = TestingSessionLocal()
    team = Team(
        name="Test Team",
        description="Test Description",
        owner_id=test_user.id
    )
    db.add(team)
    db.flush()
    
    member = TeamMember(
        team_id=team.id,
        user_id=test_user.id,
        role="owner",
        joined_at=datetime.utcnow()
    )
    db.add(member)
    db.commit()
    db.refresh(team)
    yield team
    db.delete(member)
    db.delete(team)
    db.commit()
    db.close()

@pytest.fixture
def auth_token(test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "password123"}
    )
    return response.json()["data"]["token"]

class TestUserAuthentication:
    def test_register_user(self, setup_database):
        email = f"newuser_{uuid.uuid4().hex[:8]}@example.com"
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "Password123",
                "nickname": "New User"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["user"]["email"] == email
        assert "token" in data["data"]

    def test_register_duplicate_email(self, test_user):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "Password123",
                "nickname": "Duplicate User"
            }
        )
        assert response.status_code == 409

    def test_register_weak_password(self, setup_database):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "12345",
                "nickname": "Weak User"
            }
        )
        assert response.status_code == 422

    def test_login_success(self, test_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "password123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "token" in data["data"]
        assert "refreshToken" in data["data"]

    def test_login_invalid_password(self, test_user):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "wrongpassword"}
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, setup_database):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "password123"}
        )
        assert response.status_code == 401

    def test_refresh_token(self, test_user):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "password123"}
        )
        refresh_token = login_response.json()["data"]["refreshToken"]
        
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refreshToken": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "token" in data["data"]

    def test_logout(self, test_user):
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "password123"}
        )
        auth_token = login_response.json()["data"]["token"]
        refresh_token = login_response.json()["data"]["refreshToken"]
        
        response = client.post(
            "/api/v1/auth/logout",
            json={"refreshToken": refresh_token},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

class TestUserProfile:
    def test_get_profile(self, auth_token, test_user):
        response = client.get(
            "/api/v1/users/profile",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == test_user.email

    def test_update_profile(self, auth_token):
        response = client.put(
            "/api/v1/users/profile",
            json={"nickname": "Updated Nickname"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["nickname"] == "Updated Nickname"

    def test_update_password(self, auth_token):
        response = client.put(
            "/api/v1/users/password",
            json={"oldPassword": "password123", "newPassword": "NewPassword123"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_update_password_wrong_old(self, auth_token):
        response = client.put(
            "/api/v1/users/password",
            json={"oldPassword": "wrongpassword", "newPassword": "NewPassword123"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 401

class TestTeamManagement:
    def test_create_team(self, auth_token, setup_database):
        db = TestingSessionLocal()
        email = f"createteam_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash=get_password_hash("password123"),
            nickname="Create Team User",
            status=1
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "password123"}
        )
        token = login_response.json()["data"]["token"]
        
        response = client.post(
            "/api/v1/teams",
            json={"name": "New Team", "description": "Test Team Description"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "New Team"
        
        db.close()

    def test_get_teams(self, auth_token, test_team):
        response = client.get(
            "/api/v1/teams",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1

    def test_get_team_detail(self, auth_token, test_team):
        response = client.get(
            f"/api/v1/teams/{test_team.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Test Team"

    def test_update_team(self, auth_token, test_team):
        response = client.put(
            f"/api/v1/teams/{test_team.id}",
            json={"name": "Updated Team Name"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Team Name"

    def test_delete_team(self, setup_database):
        db = TestingSessionLocal()
        email = f"deleteteam_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            email=email,
            password_hash=get_password_hash("password123"),
            nickname="Delete Team User",
            status=1
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        team = Team(
            name="Delete Team",
            description="To be deleted",
            owner_id=user.id
        )
        db.add(team)
        db.flush()
        
        member = TeamMember(
            team_id=team.id,
            user_id=user.id,
            role="owner",
            joined_at=datetime.utcnow()
        )
        db.add(member)
        db.commit()
        db.refresh(team)
        
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "password123"}
        )
        token = login_response.json()["data"]["token"]
        
        response = client.delete(
            f"/api/v1/teams/{team.id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        db.close()

    def test_add_team_member(self, auth_token, test_team):
        db = TestingSessionLocal()
        email = f"member_{uuid.uuid4().hex[:8]}@example.com"
        new_user = User(
            email=email,
            password_hash=get_password_hash("password123"),
            nickname="Member User",
            status=1
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        response = client.post(
            f"/api/v1/teams/{test_team.id}/members",
            json={"email": email, "role": "member"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        db.close()

    def test_get_team_members(self, auth_token, test_team):
        response = client.get(
            f"/api/v1/teams/{test_team.id}/members",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] >= 1

class TestSecurity:
    def test_access_protected_route_without_token(self, setup_database):
        response = client.get("/api/v1/users/profile")
        assert response.status_code == 403

    def test_access_protected_route_with_invalid_token(self, setup_database):
        response = client.get(
            "/api/v1/users/profile",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    def test_access_team_without_permission(self, auth_token, test_user, setup_database):
        db = TestingSessionLocal()
        email = f"another_{uuid.uuid4().hex[:8]}@example.com"
        another_user = User(
            email=email,
            password_hash=get_password_hash("password123"),
            nickname="Another User",
            status=1
        )
        db.add(another_user)
        db.commit()
        db.refresh(another_user)
        
        team = Team(
            name="Another Team",
            description="Another Team Description",
            owner_id=another_user.id
        )
        db.add(team)
        db.flush()
        
        member = TeamMember(
            team_id=team.id,
            user_id=another_user.id,
            role="owner",
            joined_at=datetime.utcnow()
        )
        db.add(member)
        db.commit()
        db.refresh(team)
        
        response = client.get(
            f"/api/v1/teams/{team.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 403
        
        db.delete(member)
        db.delete(team)
        db.delete(another_user)
        db.commit()
        db.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])