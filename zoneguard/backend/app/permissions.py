"""Server-side role-based access control. The frontend hides controls, but THIS is the gate."""

from __future__ import annotations

from enum import Enum

from .models import Role


class Perm(str, Enum):
    VIEW = "view"  # read cameras, zones, rules, events, incidents (no secrets ever)
    VIEW_AUDIT = "view_audit"
    MANAGE_ORG = "manage_org"  # org settings, privacy, retention, feature flags
    MANAGE_MEMBERS = "manage_members"
    MANAGE_SITES = "manage_sites"
    MANAGE_CAMERAS = "manage_cameras"
    MANAGE_EDGE = "manage_edge"
    MANAGE_ZONES_RULES = "manage_zones_rules"
    UPLOAD_VIDEO = "upload_video"
    RUN_ANALYSIS = "run_analysis"
    REVIEW_INCIDENTS = "review_incidents"
    DELETE_MEDIA = "delete_media"
    RUN_EVALUATION = "run_evaluation"


ROLE_PERMISSIONS: dict[str, set[Perm]] = {
    Role.ORG_ADMIN: set(Perm),
    Role.SITE_MANAGER: {
        Perm.VIEW, Perm.MANAGE_SITES, Perm.MANAGE_CAMERAS, Perm.MANAGE_EDGE, Perm.MANAGE_ZONES_RULES,
        Perm.UPLOAD_VIDEO, Perm.RUN_ANALYSIS, Perm.REVIEW_INCIDENTS, Perm.DELETE_MEDIA, Perm.RUN_EVALUATION,
    },
    Role.SECURITY_REVIEWER: {Perm.VIEW, Perm.REVIEW_INCIDENTS, Perm.RUN_ANALYSIS},
    Role.AUDITOR: {Perm.VIEW, Perm.VIEW_AUDIT},
}


def has_perm(role: str, perm: Perm) -> bool:
    return perm in ROLE_PERMISSIONS.get(role, set())
