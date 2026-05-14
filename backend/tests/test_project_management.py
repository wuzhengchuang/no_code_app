import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import uuid

os.environ["DATABASE_URL"] = "mysql+pymysql://root:root@localhost:3306/nocode_app_test?charset=utf8mb4"

from src.main import app
from src.db.session import Base, get_db
from src.models.user import User, UserSession
from src.models.team import Team, TeamMember
from src.models.project import Project, ProjectCollaborator, ProjectTemplate, Page, ProjectSnapshot, ProjectShare
from src.core.security import get_password_hash

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:root@localhost:3306/nocode_app_test?charset=utf8mb4"

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
        if get_db in app.dependency_overrides:
            del app.dependency_overrides[get_db]

@pytest.fixture(scope="function")
def disable_rate_limit():
    if hasattr(app.state, 'limiter'):
        original_enabled = app.state.limiter.enabled
        app.state.limiter.enabled = False
        yield
        app.state.limiter.enabled = original_enabled
    else:
        yield

@pytest.fixture(scope="function")
def client(db_session, disable_rate_limit):
    return TestClient(app)

@pytest.fixture(scope="function")
def test_user(db_session):
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=email,
        password_hash=get_password_hash("password123"),
        nickname="Test User",
        status=1
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_user2(db_session):
    email = f"test2_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=email,
        password_hash=get_password_hash("password123"),
        nickname="Test User 2",
        status=1
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_project(db_session, test_user):
    project = Project(
        name="Test Project",
        description="Test Description",
        owner_id=test_user.id,
        template_type="blank",
        target_platforms=["h5", "wechat_miniapp"],
        status="active",
        config={},
        project_data={
            "pages": [],
            "apis": [],
            "dataModels": [],
            "eventBindings": [],
            "globalStates": []
        },
        version=1,
        last_edited_by=test_user.id,
        last_edited_at=datetime.utcnow()
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project

@pytest.fixture(scope="function")
def auth_token(client, test_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "password123"}
    )
    return response.json()["data"]["token"]

@pytest.fixture(scope="function")
def auth_token_user2(client, test_user2):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": test_user2.email, "password": "password123"}
    )
    return response.json()["data"]["token"]

@pytest.fixture(scope="function")
def test_template(db_session, test_user):
    template = ProjectTemplate(
        name="Test Template",
        description="A test template",
        category="business",
        template_data={
            "pages": [],
            "apis": [],
            "dataModels": [],
            "eventBindings": [],
            "globalStates": []
        },
        target_platforms=["h5"],
        is_public=True,
        created_by=test_user.id
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template

@pytest.fixture(scope="function")
def test_collaborator(db_session, test_project, test_user2):
    collaborator = ProjectCollaborator(
        project_id=test_project.id,
        user_id=test_user2.id,
        permission="write",
        invited_by=test_project.owner_id,
        joined_at=datetime.utcnow()
    )
    db_session.add(collaborator)
    db_session.commit()
    db_session.refresh(collaborator)
    return collaborator

class TestProjectCRUD:
    def test_create_project(self, client, auth_token, test_user):
        response = client.post(
            "/api/v1/projects",
            json={
                "name": "New Project",
                "description": "Project Description",
                "template_type": "blank",
                "target_platforms": ["h5", "wechat_miniapp"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "New Project"
        assert data["data"]["status"] == "draft"
        assert data["data"]["owner_id"] == test_user.id

    def test_create_project_with_template(self, client, auth_token, test_template):
        response = client.post(
            "/api/v1/projects",
            json={
                "name": "Project From Template",
                "description": "From template",
                "template_type": "from_template",
                "template_id": test_template.id,
                "target_platforms": ["h5"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Project From Template"
        assert data["data"]["template_type"] == "from_template"

    def test_create_project_invalid_platform(self, client, auth_token):
        response = client.post(
            "/api/v1/projects",
            json={
                "name": "Invalid Platform",
                "description": "Test",
                "target_platforms": ["invalid_platform"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422

    def test_create_project_empty_name(self, client, auth_token):
        response = client.post(
            "/api/v1/projects",
            json={
                "name": "",
                "target_platforms": ["h5"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422

    def test_list_projects(self, client, auth_token, test_project):
        response = client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] >= 1
        assert len(data["data"]["items"]) >= 1

    def test_list_projects_with_filters(self, client, auth_token, test_project):
        response = client.get(
            f"/api/v1/projects?status=active&keyword={test_project.name}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] >= 1

    def test_list_projects_pagination(self, client, auth_token, test_user, db_session):
        for i in range(25):
            project = Project(
                name=f"Project {i}",
                description=f"Description {i}",
                owner_id=test_user.id,
                template_type="blank",
                target_platforms=["h5"],
                status="draft",
                config={},
                project_data={},
                version=1
            )
            db_session.add(project)
        db_session.commit()
        
        response = client.get(
            "/api/v1/projects?page=2&page_size=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["page"] == 2
        assert len(data["data"]["items"]) == 10

    def test_list_projects_sort_asc(self, client, auth_token, test_user, db_session):
        for i in range(3):
            project = Project(
                name=f"Project {i}",
                owner_id=test_user.id,
                template_type="blank",
                target_platforms=["h5"],
                status="draft"
            )
            db_session.add(project)
        db_session.commit()
        
        response = client.get(
            "/api/v1/projects?sort_order=asc",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_update_project_nonexistent(self, client, auth_token):
        response = client.put(
            "/api/v1/projects/99999",
            json={"name": "Updated"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404

    def test_delete_project_nonexistent(self, client, auth_token):
        response = client.delete(
            "/api/v1/projects/99999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404

    def test_copy_project_nonexistent(self, client, auth_token):
        response = client.post(
            "/api/v1/projects/99999/copy",
            json={"name": "Copied Project"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404

    def test_export_project_nonexistent(self, client, auth_token):
        response = client.post(
            "/api/v1/projects/99999/export",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404

    def test_get_project(self, client, auth_token, test_project):
        response = client.get(
            f"/api/v1/projects/{test_project.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == test_project.id
        assert data["data"]["name"] == test_project.name

    def test_get_project_not_found(self, client, auth_token):
        response = client.get(
            "/api/v1/projects/99999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404

    def test_get_project_no_permission(self, client, auth_token_user2, test_project):
        response = client.get(
            f"/api/v1/projects/{test_project.id}",
            headers={"Authorization": f"Bearer {auth_token_user2}"}
        )
        assert response.status_code == 403

    def test_update_project(self, client, auth_token, test_project):
        response = client.put(
            f"/api/v1/projects/{test_project.id}",
            json={
                "name": "Updated Project",
                "description": "Updated Description",
                "status": "archived"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Updated Project"
        assert data["data"]["status"] == "archived"

    def test_update_project_no_permission(self, client, auth_token_user2, test_project):
        response = client.put(
            f"/api/v1/projects/{test_project.id}",
            json={"name": "Hacked"},
            headers={"Authorization": f"Bearer {auth_token_user2}"}
        )
        assert response.status_code == 403

    def test_update_project_not_found(self, client, auth_token):
        response = client.put(
            "/api/v1/projects/99999",
            json={"name": "Not Found"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404

    def test_update_project_invalid_status(self, client, auth_token, test_project):
        response = client.put(
            f"/api/v1/projects/{test_project.id}",
            json={"status": "invalid_status"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422

    def test_update_project_data(self, client, auth_token, test_project):
        response = client.put(
            f"/api/v1/projects/{test_project.id}/data",
            json={
                "version": 1,
                "project_data": {
                    "pages": [{"name": "Home"}],
                    "apis": [],
                    "dataModels": [],
                    "eventBindings": [],
                    "globalStates": []
                }
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["version"] == 2

    def test_update_project_data_version_conflict(self, client, auth_token, test_project):
        response = client.put(
            f"/api/v1/projects/{test_project.id}/data",
            json={
                "version": 99,
                "project_data": {"pages": []}
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 409

    def test_delete_project(self, client, auth_token, test_project):
        project_id = test_project.id
        response = client.delete(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_project_not_found(self, client, auth_token):
        response = client.delete(
            "/api/v1/projects/99999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404

    def test_delete_project_no_permission(self, client, auth_token_user2, test_project):
        response = client.delete(
            f"/api/v1/projects/{test_project.id}",
            headers={"Authorization": f"Bearer {auth_token_user2}"}
        )
        assert response.status_code == 403

class TestProjectCopyExportImport:
    def test_copy_project(self, client, auth_token, test_project):
        response = client.post(
            f"/api/v1/projects/{test_project.id}/copy",
            json={"name": "Copied Project"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Copied Project"
        assert data["data"]["status"] == "draft"
        assert data["data"]["id"] != test_project.id

    def test_copy_project_no_permission(self, client, auth_token_user2, test_project):
        response = client.post(
            f"/api/v1/projects/{test_project.id}/copy",
            json={"name": "Copy Without Permission"},
            headers={"Authorization": f"Bearer {auth_token_user2}"}
        )
        assert response.status_code == 403

    def test_copy_project_not_found(self, client, auth_token):
        response = client.post(
            "/api/v1/projects/99999/copy",
            json={"name": "Copy"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404

    def test_export_project(self, client, auth_token, test_project):
        response = client.post(
            f"/api/v1/projects/{test_project.id}/export",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "name" in data["data"]
        assert "project_data" in data["data"]

    def test_export_project_no_permission(self, client, auth_token_user2, test_project):
        response = client.post(
            f"/api/v1/projects/{test_project.id}/export",
            headers={"Authorization": f"Bearer {auth_token_user2}"}
        )
        assert response.status_code == 403

    def test_import_project(self, client, auth_token):
        import_data = {
            "name": "Imported Project",
            "description": "Imported from export",
            "target_platforms": ["h5"],
            "config": {},
            "project_data": {
                "pages": [{"name": "Home", "path": "/home"}],
                "apis": [],
                "dataModels": [],
                "eventBindings": [],
                "globalStates": []
            }
        }
        response = client.post(
            "/api/v1/projects/import",
            json=import_data,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "Imported Project"

class TestProjectTemplates:
    def test_list_templates(self, client, auth_token, test_template):
        response = client.get(
            "/api/v1/projects/templates",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] >= 1

    def test_list_templates_by_category(self, client, auth_token, test_template):
        response = client.get(
            f"/api/v1/projects/templates?category={test_template.category}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

class TestProjectCollaborators:
    def test_add_collaborator(self, client, auth_token, test_project, test_user2):
        response = client.post(
            f"/api/v1/projects/{test_project.id}/collaborators",
            json={"user_id": test_user2.id, "permission": "write"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["user_id"] == test_user2.id

    def test_add_collaborator_no_permission(self, client, auth_token_user2, test_project, test_user):
        response = client.post(
            f"/api/v1/projects/{test_project.id}/collaborators",
            json={"user_id": test_user.id, "permission": "write"},
            headers={"Authorization": f"Bearer {auth_token_user2}"}
        )
        assert response.status_code == 403

    def test_get_collaborators(self, client, auth_token, test_project, test_collaborator):
        response = client.get(
            f"/api/v1/projects/{test_project.id}/collaborators",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["total"] >= 1

    def test_update_collaborator_permission(self, client, auth_token, test_project, test_collaborator):
        response = client.put(
            f"/api/v1/projects/{test_project.id}/collaborators/{test_collaborator.id}",
            json={"permission": "admin"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["permission"] == "admin"

    def test_remove_collaborator(self, client, auth_token, test_project, test_collaborator):
        response = client.delete(
            f"/api/v1/projects/{test_project.id}/collaborators/{test_collaborator.id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_add_collaborator_self(self, client, auth_token, test_project):
        response = client.post(
            f"/api/v1/projects/{test_project.id}/collaborators",
            json={"user_id": 99999, "permission": "write"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "USER_NOT_FOUND"

    def test_add_collaborator_invalid_user(self, client, auth_token, test_project, test_user):
        response = client.post(
            f"/api/v1/projects/{test_project.id}/collaborators",
            json={"user_id": test_user.id, "permission": "write"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "INVALID_REQUEST"

    def test_update_nonexistent_collaborator(self, client, auth_token, test_project):
        response = client.put(
            f"/api/v1/projects/{test_project.id}/collaborators/99999",
            json={"permission": "admin"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "COLLABORATOR_NOT_FOUND"

    def test_remove_nonexistent_collaborator(self, client, auth_token, test_project):
        response = client.delete(
            f"/api/v1/projects/{test_project.id}/collaborators/99999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "COLLABORATOR_NOT_FOUND"

class TestProjectPermissions:
    def test_collaborator_can_read(self, client, auth_token_user2, test_project, test_collaborator):
        response = client.get(
            f"/api/v1/projects/{test_project.id}",
            headers={"Authorization": f"Bearer {auth_token_user2}"}
        )
        assert response.status_code == 200

    def test_collaborator_can_update_data(self, client, auth_token_user2, test_project, test_collaborator):
        response = client.put(
            f"/api/v1/projects/{test_project.id}/data",
            json={
                "version": 1,
                "project_data": {"pages": []}
            },
            headers={"Authorization": f"Bearer {auth_token_user2}"}
        )
        assert response.status_code == 200

    def test_read_only_cannot_update(self, client, auth_token_user2, test_project, test_user, db_session):
        collaborator = ProjectCollaborator(
            project_id=test_project.id,
            user_id=test_user.id,
            permission="read",
            invited_by=test_project.owner_id,
            joined_at=datetime.utcnow()
        )
        db_session.add(collaborator)
        db_session.commit()
        
        response = client.put(
            f"/api/v1/projects/{test_project.id}/data",
            json={
                "version": 1,
                "project_data": {"pages": []}
            },
            headers={"Authorization": f"Bearer {auth_token_user2}"}
        )
        assert response.status_code == 403

class TestProjectSharing:
    def test_create_share(self, client, auth_token, test_project):
        response = client.post(
            f"/api/v1/projects/{test_project.id}/shares",
            json={"permission": "view"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "share_token" in data["data"]

    def test_create_share_no_permission(self, client, auth_token_user2, test_project):
        response = client.post(
            f"/api/v1/projects/{test_project.id}/shares",
            json={"permission": "view"},
            headers={"Authorization": f"Bearer {auth_token_user2}"}
        )
        assert response.status_code == 403

    def test_get_shares(self, client, auth_token, test_project):
        client.post(
            f"/api/v1/projects/{test_project.id}/shares",
            json={"permission": "view"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        response = client.get(
            f"/api/v1/projects/{test_project.id}/shares",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_share(self, client, auth_token, test_project):
        create_response = client.post(
            f"/api/v1/projects/{test_project.id}/shares",
            json={"permission": "view"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        share_id = create_response.json()["data"]["id"]
        
        response = client.delete(
            f"/api/v1/projects/{test_project.id}/shares/{share_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

class TestProjectSnapshots:
    def test_create_snapshot(self, client, auth_token, test_project):
        response = client.post(
            f"/api/v1/projects/{test_project.id}/snapshots",
            json={"version_name": "v1.0.0", "description": "Initial version"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["version_name"] == "v1.0.0"

    def test_list_snapshots(self, client, auth_token, test_project):
        client.post(
            f"/api/v1/projects/{test_project.id}/snapshots",
            json={"version_name": "v1.0.0"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        response = client.get(
            f"/api/v1/projects/{test_project.id}/snapshots",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_snapshot_detail(self, client, auth_token, test_project):
        create_response = client.post(
            f"/api/v1/projects/{test_project.id}/snapshots",
            json={"version_name": "v1.0.0"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        snapshot_id = create_response.json()["data"]["id"]
        
        response = client.get(
            f"/api/v1/projects/{test_project.id}/snapshots/{snapshot_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_snapshot(self, client, auth_token, test_project):
        create_response = client.post(
            f"/api/v1/projects/{test_project.id}/snapshots",
            json={"version_name": "v1.0.0"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        snapshot_id = create_response.json()["data"]["id"]
        
        response = client.delete(
            f"/api/v1/projects/{test_project.id}/snapshots/{snapshot_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_create_snapshot_no_permission(self, client, auth_token_user2, test_project):
        response = client.post(
            f"/api/v1/projects/{test_project.id}/snapshots",
            json={"version_name": "v1.0.0"},
            headers={"Authorization": f"Bearer {auth_token_user2}"}
        )
        assert response.status_code == 403

    def test_create_snapshot_nonexistent_project(self, client, auth_token):
        response = client.post(
            "/api/v1/projects/99999/snapshots",
            json={"version_name": "v1.0.0"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "PROJECT_NOT_FOUND"

    def test_list_snapshots_no_permission(self, client, auth_token_user2, test_project):
        response = client.get(
            f"/api/v1/projects/{test_project.id}/snapshots",
            headers={"Authorization": f"Bearer {auth_token_user2}"}
        )
        assert response.status_code == 403

    def test_get_snapshot_no_permission(self, client, auth_token_user2, test_project):
        response = client.get(
            f"/api/v1/projects/{test_project.id}/snapshots/1",
            headers={"Authorization": f"Bearer {auth_token_user2}"}
        )
        assert response.status_code == 403

    def test_get_nonexistent_snapshot(self, client, auth_token, test_project):
        response = client.get(
            f"/api/v1/projects/{test_project.id}/snapshots/99999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404

    def test_restore_snapshot(self, client, auth_token, test_project):
        create_response = client.post(
            f"/api/v1/projects/{test_project.id}/snapshots",
            json={"version_name": "v1.0.0"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        snapshot_id = create_response.json()["data"]["id"]
        
        response = client.post(
            f"/api/v1/projects/{test_project.id}/snapshots/{snapshot_id}/restore",
            json={},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_nonexistent_snapshot(self, client, auth_token, test_project):
        response = client.delete(
            f"/api/v1/projects/{test_project.id}/snapshots/99999",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 404

    def test_delete_snapshot_no_permission(self, client, auth_token_user2, test_project):
        response = client.delete(
            f"/api/v1/projects/{test_project.id}/snapshots/1",
            headers={"Authorization": f"Bearer {auth_token_user2}"}
        )
        assert response.status_code == 403

class TestProjectAdditionalCoverage:
    def test_project_with_page_copy(self, client, auth_token, test_project, db_session):
        page = Page(
            project_id=test_project.id,
            name="Home",
            path="/home",
            is_home=True,
            layout_config={},
            components=[],
            sort_order=1
        )
        db_session.add(page)
        db_session.commit()
        
        response = client.post(
            f"/api/v1/projects/{test_project.id}/copy",
            json={"name": "Copied Project with Page"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        copied_project_id = data["data"]["id"]
        
        response = client.post(
            f"/api/v1/projects/{copied_project_id}/export",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        export_data = response.json()
        assert len(export_data["data"]["pages"]) == 1

    def test_update_project_data_version_conflict(self, client, auth_token, test_project):
        response = client.put(
            f"/api/v1/projects/{test_project.id}/data",
            json={"version": 999, "project_data": {"pages": []}},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["code"] == "VERSION_CONFLICT"

class TestProjectValidation:
    def test_project_name_max_length(self, client, auth_token):
        long_name = "a" * 200
        response = client.post(
            "/api/v1/projects",
            json={
                "name": long_name,
                "target_platforms": ["h5"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422

    def test_project_description_max_length(self, client, auth_token):
        long_desc = "a" * 2000
        response = client.post(
            "/api/v1/projects",
            json={
                "name": "Test",
                "description": long_desc,
                "target_platforms": ["h5"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422

    def test_invalid_template_type(self, client, auth_token):
        response = client.post(
            "/api/v1/projects",
            json={
                "name": "Test",
                "template_type": "invalid",
                "target_platforms": ["h5"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 422

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
