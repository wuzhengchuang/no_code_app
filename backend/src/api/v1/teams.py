from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from src.db.session import get_db
from src.core.dependencies import get_current_user, require_team_role
from src.models.user import User
from src.schemas.team import (
    TeamCreate, TeamUpdate, TeamResponse, TeamListResponse,
    TeamMemberAdd, TeamMemberUpdate, TeamMemberResponse,
    TeamOwnershipTransfer, TeamMemberListResponse
)
from src.services.team_service import TeamService

router = APIRouter()

@router.post("", response_model=Dict[str, Any], status_code=201)
async def create_team(
    data: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team_service = TeamService(db)
    result = team_service.create_team(current_user.id, data)
    return {
        "success": True,
        "data": result.model_dump(),
        "message": "创建成功"
    }

@router.get("", response_model=Dict[str, Any])
async def get_teams(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team_service = TeamService(db)
    result = team_service.get_user_teams(current_user.id)
    return {
        "success": True,
        "data": [team.dict() for team in result],
        "message": "获取成功"
    }

@router.get("/{team_id}", response_model=Dict[str, Any])
async def get_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _ = Depends(require_team_role("viewer"))
):
    team_service = TeamService(db)
    result = team_service.get_team_detail(team_id)
    return {
        "success": True,
        "data": result.dict(),
        "message": "获取成功"
    }

@router.put("/{team_id}", response_model=Dict[str, Any])
async def update_team(
    team_id: int,
    data: TeamUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _ = Depends(require_team_role("admin"))
):
    team_service = TeamService(db)
    result = team_service.update_team(team_id, data)
    return {
        "success": True,
        "data": result.dict(),
        "message": "更新成功"
    }

@router.delete("/{team_id}", response_model=Dict[str, Any])
async def delete_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _ = Depends(require_team_role("owner"))
):
    team_service = TeamService(db)
    team_service.delete_team(team_id)
    return {
        "success": True,
        "data": None,
        "message": "删除成功"
    }

@router.get("/{team_id}/members", response_model=Dict[str, Any])
async def get_team_members(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _ = Depends(require_team_role("viewer"))
):
    team_service = TeamService(db)
    result = team_service.get_team_members(team_id)
    return {
        "success": True,
        "data": result.dict(),
        "message": "获取成功"
    }

@router.post("/{team_id}/members", response_model=Dict[str, Any])
async def add_team_member(
    team_id: int,
    data: TeamMemberAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _ = Depends(require_team_role("admin"))
):
    team_service = TeamService(db)
    result = team_service.add_team_member(team_id, current_user.id, data)
    return {
        "success": True,
        "data": result.dict(),
        "message": "添加成功"
    }

@router.put("/{team_id}/members/{user_id}", response_model=Dict[str, Any])
async def update_member_role(
    team_id: int,
    user_id: int,
    data: TeamMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _ = Depends(require_team_role("admin"))
):
    team_service = TeamService(db)
    team_service.update_member_role(team_id, user_id, data)
    return {
        "success": True,
        "data": None,
        "message": "更新成功"
    }

@router.delete("/{team_id}/members/{user_id}", response_model=Dict[str, Any])
async def remove_team_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _ = Depends(require_team_role("admin"))
):
    team_service = TeamService(db)
    team_service.remove_team_member(team_id, user_id)
    return {
        "success": True,
        "data": None,
        "message": "移除成功"
    }

@router.put("/{team_id}/ownership", response_model=Dict[str, Any])
async def transfer_ownership(
    team_id: int,
    data: TeamOwnershipTransfer,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _ = Depends(require_team_role("owner"))
):
    team_service = TeamService(db)
    team_service.transfer_ownership(team_id, current_user.id, data)
    return {
        "success": True,
        "data": None,
        "message": "转让成功"
    }
