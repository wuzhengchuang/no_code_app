#!/usr/bin/env python3
"""
模块二简单测试脚本 - 验证项目管理核心功能
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy import event
from src.db.session import Base, engine, SessionLocal
from src.models.user import User
from src.models.project import Project, ProjectCollaborator, ProjectSnapshot, ProjectShare
from src.core.security import get_password_hash

@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    if 'UPDATE projects' in statement or 'INSERT INTO project_snapshots' in statement:
        print(f'\n=== SQL ===')
        print(f'Statement: {statement[:200]}...')
        print(f'Params: {params}')

def test_project_models():
    """测试项目模型"""
    print("📁 测试项目模型...")
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()

        test_email = "test_project_user@example.com"
        existing = db.query(User).filter(User.email == test_email).first()
        if existing:
            db.delete(existing)
            db.commit()

        user = User(
            email=test_email,
            password_hash=get_password_hash("TestPassword123"),
            nickname="项目测试用户",
            status=1
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f'User created: id={user.id}')

        project = Project(
            name="测试项目",
            description="这是一个测试项目",
            owner_id=user.id,
            template_type="blank",
            target_platforms=["web"],
            status="active"
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        print(f'Project created: id={project.id}, owner_id={project.owner_id}')

        print('\n=== Creating Snapshot ===')
        snapshot = ProjectSnapshot(
            project_id=project.id,
            version_name="v1.0",
            description="初始版本",
            snapshot_data={"pages": [], "components": []},
            project_version=1,
            created_by=user.id
        )
        db.add(snapshot)
        db.commit()
        print('Snapshot commit successful')

        print('\n=== Creating Share ===')
        import uuid
        share = ProjectShare(
            project_id=project.id,
            share_token=str(uuid.uuid4()),
            permission="view",
            is_password_protected=False,
            created_by=user.id
        )
        db.add(share)
        db.commit()
        print('Share commit successful')

        print('\n=== Creating Collaborator ===')
        collaborator_email = "collaborator@example.com"
        existing_collab = db.query(User).filter(User.email == collaborator_email).first()
        if existing_collab:
            db.delete(existing_collab)
            db.commit()

        collaborator = User(
            email=collaborator_email,
            password_hash=get_password_hash("CollabPassword123"),
            nickname="协作用户",
            status=1
        )
        db.add(collaborator)
        db.commit()
        db.refresh(collaborator)

        project_collab = ProjectCollaborator(
            project_id=project.id,
            user_id=collaborator.id,
            permission="edit",
            invited_by=user.id
        )
        db.add(project_collab)
        db.commit()
        print('Collaborator commit successful')

        db.delete(project_collab)
        db.delete(share)
        db.delete(snapshot)
        db.delete(project)
        db.delete(collaborator)
        db.delete(user)
        db.commit()
        db.close()

        print("\n🎉 所有项目管理模型测试通过！")
        return True

    except Exception as e:
        print(f"❌ 项目模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("🚀 模块二（项目管理子模块）简单测试")
    print("=" * 60)

    tests = [
        ("项目管理模型", test_project_models),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {name}测试异常: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()

    print("=" * 60)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())