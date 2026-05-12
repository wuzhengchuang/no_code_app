from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException, status
from typing import List

from src.models.team import Team, TeamMember
from src.models.user import User
from src.schemas.team import (
    TeamCreate, TeamUpdate, TeamResponse, TeamListResponse,
    TeamMemberAdd, TeamMemberUpdate, TeamMemberResponse,
    TeamOwnershipTransfer, TeamMemberListResponse
)
from src.schemas.user import UserBase

class TeamService:
    def __init__(self, db: Session):
        self.db = db

    def create_team(self, user_id: int, data: TeamCreate) -> TeamResponse:
        team = Team(
            name=data.name,
            description=data.description,
            owner_id=user_id
        )
        self.db.add(team)
        self.db.flush()

        team_member = TeamMember(
            team_id=team.id,
            user_id=user_id,
            role="owner",
            joined_at=datetime.utcnow()
        )
        self.db.add(team_member)

        self.db.commit()
        self.db.refresh(team)

        return TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            ownerId=team.owner_id,
            createdAt=team.created_at,
            updatedAt=team.updated_at
        )

    def get_user_teams(self, user_id: int) -> List[TeamListResponse]:
        teams = self.db.query(
            Team.id,
            Team.name,
            Team.description,
            Team.owner_id,
            Team.created_at,
            Team.updated_at,
            TeamMember.role
        ).join(TeamMember, Team.id == TeamMember.team_id)\
         .filter(TeamMember.user_id == user_id)\
         .all()

        result = []
        for team in teams:
            member_count = self.db.query(TeamMember)\
                .filter(TeamMember.team_id == team.id)\
                .count()
            
            result.append(TeamListResponse(
                id=team.id,
                name=team.name,
                description=team.description,
                ownerId=team.owner_id,
                role=team.role,
                memberCount=member_count,
                createdAt=team.created_at,
                updatedAt=team.updated_at
            ))
        
        return result

    def get_team_by_id(self, team_id: int) -> Team:
        team = self.db.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="团队不存在"
            )
        return team

    def get_team_detail(self, team_id: int) -> TeamResponse:
        team = self.get_team_by_id(team_id)
        return TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            ownerId=team.owner_id,
            createdAt=team.created_at,
            updatedAt=team.updated_at
        )

    def update_team(self, team_id: int, data: TeamUpdate) -> TeamResponse:
        team = self.get_team_by_id(team_id)
        
        if data.name is not None:
            team.name = data.name
        if data.description is not None:
            team.description = data.description
        
        self.db.commit()
        self.db.refresh(team)

        return TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            ownerId=team.owner_id,
            createdAt=team.created_at,
            updatedAt=team.updated_at
        )

    def delete_team(self, team_id: int) -> None:
        team = self.get_team_by_id(team_id)
        self.db.delete(team)
        self.db.commit()

    def get_team_members(self, team_id: int) -> TeamMemberListResponse:
        self.get_team_by_id(team_id)
        
        members = self.db.query(TeamMember, User)\
            .join(User, TeamMember.user_id == User.id)\
            .filter(TeamMember.team_id == team_id)\
            .order_by(TeamMember.joined_at.desc())\
            .all()

        member_list = []
        for member, user in members:
            member_list.append(TeamMemberResponse(
                id=member.id,
                userId=member.user_id,
                user=UserBase(
                    id=user.id,
                    email=user.email,
                    nickname=user.nickname,
                    avatarUrl=user.avatar_url
                ),
                role=member.role,
                invitedBy=member.invited_by,
                joinedAt=member.joined_at
            ))

        return TeamMemberListResponse(
            members=member_list,
            total=len(member_list)
        )

    def add_team_member(self, team_id: int, inviter_id: int, data: TeamMemberAdd) -> TeamMemberResponse:
        self.get_team_by_id(team_id)

        user = self.db.query(User).filter(User.email == data.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        existing_member = self.db.query(TeamMember)\
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == user.id)\
            .first()
        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="用户已在团队中"
            )

        team_member = TeamMember(
            team_id=team_id,
            user_id=user.id,
            role=data.role,
            invited_by=inviter_id,
            joined_at=datetime.utcnow()
        )
        self.db.add(team_member)
        self.db.commit()
        self.db.refresh(team_member)

        return TeamMemberResponse(
            id=team_member.id,
            userId=team_member.user_id,
            user=UserBase(
                id=user.id,
                email=user.email,
                nickname=user.nickname,
                avatarUrl=user.avatar_url
            ),
            role=team_member.role,
            invitedBy=team_member.invited_by,
            joinedAt=team_member.joined_at
        )

    def update_member_role(self, team_id: int, user_id: int, data: TeamMemberUpdate) -> None:
        team_member = self.db.query(TeamMember)\
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)\
            .first()

        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="团队成员不存在"
            )

        if team_member.role == "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能修改所有者角色"
            )

        team_member.role = data.role
        self.db.commit()

    def remove_team_member(self, team_id: int, user_id: int) -> None:
        team_member = self.db.query(TeamMember)\
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)\
            .first()

        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="团队成员不存在"
            )

        if team_member.role == "owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不能移除所有者"
            )

        self.db.delete(team_member)
        self.db.commit()

    def transfer_ownership(self, team_id: int, current_user_id: int, data: TeamOwnershipTransfer) -> None:
        team = self.get_team_by_id(team_id)

        if team.owner_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有所有者可以转让所有权"
            )

        if data.newOwnerId == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能转让给自己"
            )

        new_owner = self.db.query(User).filter(User.id == data.newOwnerId).first()
        if not new_owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="新所有者不存在"
            )

        existing_member = self.db.query(TeamMember)\
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == data.newOwnerId)\
            .first()
        if not existing_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="新所有者必须是团队成员"
            )

        old_owner_member = self.db.query(TeamMember)\
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user_id)\
            .first()
        if old_owner_member:
            old_owner_member.role = "admin"

        existing_member.role = "owner"
        team.owner_id = data.newOwnerId

        self.db.commit()
