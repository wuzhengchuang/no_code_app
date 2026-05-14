from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.models import Project, ProjectSnapshot
from src.schemas import SnapshotCreate, SnapshotRestoreRequest
from src.services.project_permission_service import has_project_access, ProjectPermission


def create_snapshot(
    db: Session,
    project_id: int,
    snapshot_data: SnapshotCreate,
    user_id: int
) -> Optional[ProjectSnapshot]:
    """创建项目快照"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None

    db_snapshot = ProjectSnapshot(
        project_id=project_id,
        version_name=snapshot_data.version_name,
        description=snapshot_data.description,
        snapshot_data=project.project_data or {},
        project_version=project.version,
        created_by=user_id
    )

    db.add(db_snapshot)
    db.commit()
    db.refresh(db_snapshot)
    return db_snapshot


def get_project_snapshots(
    db: Session,
    project_id: int,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[ProjectSnapshot], int]:
    """获取项目的快照列表"""
    query = db.query(ProjectSnapshot).filter(
        ProjectSnapshot.project_id == project_id
    ).order_by(desc(ProjectSnapshot.created_at))

    total = query.count()

    offset = (page - 1) * page_size
    snapshots = query.offset(offset).limit(page_size).all()

    return snapshots, total


def get_snapshot_by_id(
    db: Session,
    project_id: int,
    snapshot_id: int
) -> Optional[ProjectSnapshot]:
    """获取快照详情"""
    return db.query(ProjectSnapshot).filter(
        ProjectSnapshot.id == snapshot_id,
        ProjectSnapshot.project_id == project_id
    ).first()


def restore_snapshot(
    db: Session,
    project_id: int,
    snapshot_id: int,
    restore_data: SnapshotRestoreRequest,
    user_id: int
) -> Optional[dict]:
    """恢复到指定快照"""
    # Service层权限验证
    if not has_project_access(db, project_id, user_id, ProjectPermission.WRITE):
        return None

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None

    snapshot = db.query(ProjectSnapshot).filter(
        ProjectSnapshot.id == snapshot_id,
        ProjectSnapshot.project_id == project_id
    ).first()
    if not snapshot:
        return None

    backup_snapshot_id = None

    try:
        # 如果需要，先创建当前状态的备份
        if restore_data.create_backup:
            backup = ProjectSnapshot(
                project_id=project_id,
                version_name=f"backup_before_restore_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                description=f"恢复快照 {snapshot.version_name} 前的自动备份",
                snapshot_data=project.project_data or {},
                project_version=project.version,
                created_by=user_id
            )
            db.add(backup)
            db.flush()
            backup_snapshot_id = backup.id

        # 恢复快照数据
        project.project_data = snapshot.snapshot_data
        project.version += 1
        project.last_edited_by = user_id
        project.last_edited_at = datetime.utcnow()

        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "project_id": project_id,
        "new_version": project.version,
        "backup_snapshot_id": backup_snapshot_id
    }


def delete_snapshot(
    db: Session,
    project_id: int,
    snapshot_id: int
) -> bool:
    """删除快照"""
    snapshot = db.query(ProjectSnapshot).filter(
        ProjectSnapshot.id == snapshot_id,
        ProjectSnapshot.project_id == project_id
    ).first()

    if not snapshot:
        return False

    db.delete(snapshot)
    db.commit()
    return True


def get_latest_snapshot(
    db: Session,
    project_id: int
) -> Optional[ProjectSnapshot]:
    """获取最新的快照"""
    return db.query(ProjectSnapshot).filter(
        ProjectSnapshot.project_id == project_id
    ).order_by(desc(ProjectSnapshot.created_at)).first()
