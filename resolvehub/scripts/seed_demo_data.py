import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from pwdlib import PasswordHash
from sqlalchemy import select

from resolvehub.app.core.database import async_session_factory
from resolvehub.app.modules.comments.models import TicketComment
from resolvehub.app.modules.identity.models import User
from resolvehub.app.modules.organisations.models import (
    Department,
    Membership,
    Organisation,
)
from resolvehub.app.modules.organisations.service import create_organisation, list_roles
from resolvehub.app.modules.service_catalogue.models import ServiceCategory
from resolvehub.app.modules.sla.models import BusinessCalendar, SlaPolicy
from resolvehub.app.modules.tickets.enums import (
    CommentKind,
    SlaState,
    TicketPriority,
    TicketSource,
    TicketStatus,
)
from resolvehub.app.modules.tickets.models import Ticket

password_hasher = PasswordHash.recommended()


async def seed() -> None:
    async with async_session_factory() as session:
        existing_org = await session.scalar(
            select(Organisation).where(Organisation.slug == "acme-corp")
        )
        if existing_org:
            from resolvehub.app.modules.assets.models import AssetItem
            from resolvehub.app.modules.changes.models import ChangeRequest
            from resolvehub.app.modules.incidents.models import Incident
            from resolvehub.app.modules.knowledge.models import KnowledgeArticle
            from resolvehub.app.modules.problems.models import Problem

            inc_check = await session.scalar(
                select(Incident).where(Incident.organisation_id == existing_org.id)
            )
            if not inc_check:
                now = datetime.now(UTC)
                inc1 = Incident(
                    id=uuid4(),
                    incident_number="INC-2026-089",
                    organisation_id=existing_org.id,
                    title="Primary Payment Gateway Latency Spike (>4500ms)",
                    description="Payment microservice checkout requests taking over 4.5 seconds to complete.",
                    severity="P1 - Critical",
                    service_name="Payment Microservice",
                    status="Investigating",
                    commander_name="DevOps On-Call (Sarah Lin)",
                    impact_summary="Affecting checkout completion for 14% of enterprise web requests.",
                    created_at=now - timedelta(minutes=12),
                    updated_at=now,
                )
                inc2 = Incident(
                    id=uuid4(),
                    incident_number="INC-2026-088",
                    organisation_id=existing_org.id,
                    title="PostgreSQL Secondary Replica Replication Lag",
                    description="Replication lag reached 180 seconds on US-East read replica cluster.",
                    severity="P2 - High",
                    service_name="Database Cluster (US-East)",
                    status="Identified",
                    commander_name="Database Team (Marcus Vance)",
                    impact_summary="Read-heavy queries experiencing 2.4s delays.",
                    created_at=now - timedelta(minutes=45),
                    updated_at=now,
                )
                prb1 = Problem(
                    id=uuid4(),
                    problem_number="PRB-0042",
                    organisation_id=existing_org.id,
                    title="Intermittent Memory Exhaustion on Auth Service Containers",
                    category="Infrastructure",
                    status="Investigation",
                    root_cause="Under investigation. Suspected unclosed HTTP connection pools during peak load.",
                    workaround="Automatic pod restart configured via Kubernetes liveness probe when RAM > 85%.",
                    impacted_incidents_count=6,
                    created_at=now - timedelta(days=2),
                    updated_at=now,
                )
                chg1 = ChangeRequest(
                    id=uuid4(),
                    change_number="CHG-2026-044",
                    organisation_id=existing_org.id,
                    title="Upgrade Ingress NGINX Controllers to v1.10.1",
                    description="Upgrade edge ingress controllers to patch CVE-2026-1029.",
                    change_type="Normal",
                    risk_level="Medium",
                    status="CAB Approval",
                    owner_name="DevOps (Sarah Lin)",
                    maintenance_window="Sat 02:00 - 04:00 UTC",
                    created_at=now - timedelta(days=1),
                    updated_at=now,
                )
                ast1 = AssetItem(
                    id=uuid4(),
                    asset_tag="AST-2026-101",
                    organisation_id=existing_org.id,
                    name='Apple MacBook Pro 16" M3 Max (64GB RAM)',
                    category="Laptop",
                    status="In Use",
                    assigned_to_name="Alex Morgan",
                    serial_number="C02GX910Q1",
                    location="San Francisco HQ (Floor 3)",
                    created_at=now - timedelta(days=30),
                    updated_at=now,
                )
                kb1 = KnowledgeArticle(
                    id=uuid4(),
                    article_number="KB-1001",
                    organisation_id=existing_org.id,
                    title="Corporate GlobalProtect VPN Setup Guide",
                    slug="corporate-globalprotect-vpn-setup-guide",
                    summary="Step-by-step installation and authentication guide for macOS and Windows.",
                    content_markdown="# Corporate VPN Setup\n\n1. Download GlobalProtect v6.2.\n2. Connect to `vpn.acme.example.com`.\n3. Authenticate using Okta SSO.",
                    category="Network & VPN",
                    author_name="IT Support",
                    view_count=142,
                    helpful_count=38,
                    unhelpful_count=1,
                    created_at=now - timedelta(days=15),
                    updated_at=now,
                )
                session.add_all([inc1, inc2, prb1, chg1, ast1, kb1])
                await session.commit()
                print("Seeded ITSM module records for Acme Corp.")
            print("Demo data check complete.")
            return

        print("Seeding demo data...")
        now = datetime.now(UTC)
        pwd_hash = password_hasher.hash("DemoPassword123!")

        admin_user = User(
            id=uuid4(),
            email="admin@acme.example.com",
            display_name="Acme Admin",
            password_hash=pwd_hash,
            is_email_verified=True,
            is_active=True,
            created_at=now,
        )
        agent_user = User(
            id=uuid4(),
            email="agent@acme.example.com",
            display_name="Alex Agent",
            password_hash=pwd_hash,
            is_email_verified=True,
            is_active=True,
            created_at=now,
        )
        requester_user = User(
            id=uuid4(),
            email="requester@acme.example.com",
            display_name="Rita Requester",
            password_hash=pwd_hash,
            is_email_verified=True,
            is_active=True,
            created_at=now,
        )
        session.add_all([admin_user, agent_user, requester_user])
        await session.flush()

        org = await create_organisation(
            session, owner=admin_user, name="Acme Corp", slug="acme-corp"
        )
        roles = await list_roles(session, admin_user.id, org.id)
        role_map = {r.name: r.id for r in roles}

        session.add_all(
            [
                Membership(
                    id=uuid4(),
                    organisation_id=org.id,
                    user_id=agent_user.id,
                    role_id=role_map["Agent"],
                    is_active=True,
                    created_at=now,
                ),
                Membership(
                    id=uuid4(),
                    organisation_id=org.id,
                    user_id=requester_user.id,
                    role_id=role_map["Requester"],
                    is_active=True,
                    created_at=now,
                ),
            ]
        )

        dept_it = Department(
            id=uuid4(),
            organisation_id=org.id,
            name="IT Operations",
            description="Hardware, networking, and IT infrastructure support",
            created_at=now,
        )
        dept_eng = Department(
            id=uuid4(),
            organisation_id=org.id,
            name="Engineering",
            description="Software products and platform engineering",
            created_at=now,
        )
        session.add_all([dept_it, dept_eng])
        await session.flush()

        cat_hardware = ServiceCategory(
            id=uuid4(),
            organisation_id=org.id,
            department_id=dept_it.id,
            name="Hardware Issue",
            description="Laptops, monitors, peripherals, and office hardware",
            default_priority=TicketPriority.MEDIUM,
            is_active=True,
            created_at=now,
        )
        cat_software = ServiceCategory(
            id=uuid4(),
            organisation_id=org.id,
            department_id=dept_eng.id,
            name="Software License & Access",
            description="VPN access, IDE licenses, SaaS accounts",
            default_priority=TicketPriority.HIGH,
            is_active=True,
            created_at=now,
        )
        session.add_all([cat_hardware, cat_software])
        await session.flush()

        calendar = BusinessCalendar(
            id=uuid4(),
            organisation_id=org.id,
            name="Default Weekday Hours",
            timezone="UTC",
            weekly_hours={
                "mon": [["09:00", "17:00"]],
                "tue": [["09:00", "17:00"]],
                "wed": [["09:00", "17:00"]],
                "thu": [["09:00", "17:00"]],
                "fri": [["09:00", "17:00"]],
            },
            is_active=True,
            created_at=now,
        )
        session.add(calendar)
        await session.flush()

        sla_policy = SlaPolicy(
            id=uuid4(),
            organisation_id=org.id,
            calendar_id=calendar.id,
            category_id=cat_software.id,
            priority=TicketPriority.HIGH,
            first_response_minutes=60,
            resolution_minutes=480,
            warning_percent=80,
            is_active=True,
            created_at=now,
        )
        session.add(sla_policy)
        await session.flush()

        t1 = Ticket(
            id=uuid4(),
            ticket_number="RH-ACME-0001",
            organisation_id=org.id,
            requester_id=requester_user.id,
            department_id=dept_it.id,
            category_id=cat_hardware.id,
            title="MacBook Pro screen flickering",
            description=(
                "My secondary monitor displays flickering horizontal lines when connected via"
                " USB-C hub."
            ),
            priority=TicketPriority.MEDIUM,
            status=TicketStatus.SUBMITTED,
            source=TicketSource.WEB,
            sla_state=SlaState.NOT_STARTED,
            version=1,
            created_at=now - timedelta(hours=3),
        )

        t2 = Ticket(
            id=uuid4(),
            ticket_number="RH-ACME-0002",
            organisation_id=org.id,
            requester_id=requester_user.id,
            department_id=dept_eng.id,
            category_id=cat_software.id,
            assigned_agent_id=agent_user.id,
            title="Request for IntelliJ IDEA Ultimate license",
            description=(
                "Need IntelliJ license assigned for new project development starting this week."
            ),
            priority=TicketPriority.HIGH,
            status=TicketStatus.IN_PROGRESS,
            source=TicketSource.WEB,
            sla_state=SlaState.ACTIVE,
            first_response_deadline=now + timedelta(minutes=45),
            resolution_deadline=now + timedelta(hours=6),
            version=2,
            created_at=now - timedelta(minutes=15),
        )

        session.add_all([t1, t2])
        await session.flush()

        c1 = TicketComment(
            id=uuid4(),
            organisation_id=org.id,
            ticket_id=t2.id,
            author_id=agent_user.id,
            kind=CommentKind.PUBLIC,
            body="Hello Rita, I have requested approval for the IntelliJ license allocation.",
            created_at=now - timedelta(minutes=10),
        )
        c2 = TicketComment(
            id=uuid4(),
            organisation_id=org.id,
            ticket_id=t2.id,
            author_id=agent_user.id,
            kind=CommentKind.INTERNAL,
            body="License key pool currently has 4 unallocated keys remaining.",
            created_at=now - timedelta(minutes=9),
        )
        session.add_all([c1, c2])
        await session.flush()

        # Seed Incidents
        from resolvehub.app.modules.assets.models import AssetItem
        from resolvehub.app.modules.changes.models import ChangeRequest
        from resolvehub.app.modules.incidents.models import Incident
        from resolvehub.app.modules.knowledge.models import KnowledgeArticle
        from resolvehub.app.modules.problems.models import Problem

        inc1 = Incident(
            id=uuid4(),
            incident_number="INC-2026-089",
            organisation_id=org.id,
            title="Primary Payment Gateway Latency Spike (>4500ms)",
            description="Payment microservice checkout requests taking over 4.5 seconds to complete.",
            severity="P1 - Critical",
            service_name="Payment Microservice",
            status="Investigating",
            commander_name="DevOps On-Call (Sarah Lin)",
            impact_summary="Affecting checkout completion for 14% of enterprise web requests.",
            created_at=now - timedelta(minutes=12),
        )
        inc2 = Incident(
            id=uuid4(),
            incident_number="INC-2026-088",
            organisation_id=org.id,
            title="PostgreSQL Secondary Replica Replication Lag",
            description="Replication lag reached 180 seconds on US-East read replica cluster.",
            severity="P2 - High",
            service_name="Database Cluster (US-East)",
            status="Identified",
            commander_name="Database Team (Marcus Vance)",
            impact_summary="Read-heavy queries experiencing 2.4s delays.",
            created_at=now - timedelta(minutes=45),
        )
        session.add_all([inc1, inc2])

        # Seed Problems
        prb1 = Problem(
            id=uuid4(),
            problem_number="PRB-0042",
            organisation_id=org.id,
            title="Intermittent Memory Exhaustion on Auth Service Containers",
            category="Infrastructure",
            status="Investigation",
            root_cause="Under investigation. Suspected unclosed HTTP connection pools during peak load.",
            workaround="Automatic pod restart configured via Kubernetes liveness probe when RAM > 85%.",
            impacted_incidents_count=6,
            created_at=now - timedelta(days=2),
        )
        prb2 = Problem(
            id=uuid4(),
            problem_number="PRB-0039",
            organisation_id=org.id,
            title="Elasticsearch Index Shard Unbalance on Large Tenant Search",
            category="Search & Data",
            status="RCA Complete",
            root_cause="Primary shard routing key hotspotting multi-tenant indices.",
            workaround="Re-index with composite routing key (tenant_id + doc_type).",
            impacted_incidents_count=3,
            created_at=now - timedelta(days=5),
        )
        session.add_all([prb1, prb2])

        # Seed Changes
        chg1 = ChangeRequest(
            id=uuid4(),
            change_number="CHG-2026-044",
            organisation_id=org.id,
            title="Upgrade Ingress NGINX Controllers to v1.10.1",
            description="Upgrade edge ingress controllers to patch CVE-2026-1029.",
            change_type="Normal",
            risk_level="Medium",
            status="CAB Approval",
            owner_name="DevOps (Sarah Lin)",
            maintenance_window="Sat 02:00 - 04:00 UTC",
            created_at=now - timedelta(days=1),
        )
        session.add(chg1)

        # Seed Assets
        ast1 = AssetItem(
            id=uuid4(),
            asset_tag="AST-2026-101",
            organisation_id=org.id,
            name='Apple MacBook Pro 16" M3 Max (64GB RAM)',
            category="Laptop",
            status="In Use",
            assigned_to_name="Alex Morgan",
            serial_number="C02GX910Q1",
            location="San Francisco HQ (Floor 3)",
            created_at=now - timedelta(days=30),
        )
        ast2 = AssetItem(
            id=uuid4(),
            asset_tag="AST-2026-102",
            organisation_id=org.id,
            name='Dell UltraSharp 27" 4K USB-C Hub Monitor',
            category="Display",
            status="In Use",
            assigned_to_name="Riya Sharma",
            serial_number="CN-09821-A1",
            location="London Office",
            created_at=now - timedelta(days=20),
        )
        session.add_all([ast1, ast2])

        # Seed Knowledge Base Articles
        kb1 = KnowledgeArticle(
            id=uuid4(),
            article_number="KB-1001",
            organisation_id=org.id,
            title="Corporate GlobalProtect VPN Setup Guide",
            slug="corporate-globalprotect-vpn-setup-guide",
            summary="Step-by-step installation and authentication guide for macOS and Windows.",
            content_markdown="# Corporate VPN Setup\n\n1. Download GlobalProtect v6.2.\n2. Connect to `vpn.acme.example.com`.\n3. Authenticate using Okta SSO.",
            category="Network & VPN",
            author_name="IT Support",
            view_count=142,
            helpful_count=38,
            unhelpful_count=1,
            created_at=now - timedelta(days=15),
        )
        session.add(kb1)

        await session.commit()
        print("Demo data seeded successfully:")
        print("  Organisation: Acme Corp (acme-corp)")
        print("  Admin: admin@acme.example.com (Password: DemoPassword123!)")
        print("  Agent: agent@acme.example.com (Password: DemoPassword123!)")
        print("  Requester: requester@acme.example.com (Password: DemoPassword123!)")


if __name__ == "__main__":
    asyncio.run(seed())
