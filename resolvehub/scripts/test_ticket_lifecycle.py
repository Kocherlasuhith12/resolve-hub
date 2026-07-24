#!/usr/bin/env python3
"""Automated E2E Ticket Creation & Lifecycle Resolution Test Script for ResolveHub"""

import asyncio
from uuid import uuid4
import httpx


LIVE_API_BASE = "https://resolvehub-api-suhith.onrender.com/api/v1"
TEST_EMAIL = "test-agent-sravan@resolvehub.dev"
TEST_PASSWORD = "Password123!"


async def run_e2e_ticket_flow():
    print("=" * 70)
    print("🚀 RESOLVEHUB LIVE E2E TICKET CREATION & AUTOMATIC RESOLUTION TEST")
    print("=" * 70)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Login or Register
        print("\n🔑 Step 1: Authenticating user account...")
        login_resp = await client.post(
            f"{LIVE_API_BASE}/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        )

        if login_resp.status_code != 200:
            print("   Registration needed. Creating test account...")
            reg_resp = await client.post(
                f"{LIVE_API_BASE}/auth/register",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                    "display_name": "Sravan Kocherla",
                },
            )
            print(f"   Registration response: {reg_resp.status_code}")
            login_resp = await client.post(
                f"{LIVE_API_BASE}/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            )

        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        tokens = login_resp.json()
        access_token = tokens["access_token"]
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        print("   ✅ Authentication successful! JWT access token retrieved.")

        # 2. Get User Profile & Organisation
        print("\n🏢 Step 2: Fetching active workspace & organisation ID...")
        me_resp = await client.get(f"{LIVE_API_BASE}/auth/me", headers=headers)
        assert me_resp.status_code == 200, f"Failed to get user profile: {me_resp.text}"
        user_data = me_resp.json()
        print(f"   User: {user_data['display_name']} ({user_data['email']})")

        orgs_resp = await client.get(f"{LIVE_API_BASE}/organisations", headers=headers)
        if orgs_resp.status_code != 200 or not orgs_resp.json():
            print("   Creating new organisation workspace...")
            create_org_resp = await client.post(
                f"{LIVE_API_BASE}/organisations",
                headers=headers,
                json={"name": "Kocherla Ops Hub", "slug": "kocherla-ops"},
            )
            org_id = create_org_resp.json()["id"]
        else:
            org_id = orgs_resp.json()[0]["id"]

        print(f"   ✅ Active Organisation ID: {org_id}")

        # 3. Get or Create Service Category
        print("\n📂 Step 3: Fetching service catalogue categories...")
        cat_resp = await client.get(
            f"{LIVE_API_BASE}/organisations/{org_id}/categories", headers=headers
        )
        categories = cat_resp.json()
        if not categories:
            print("   Fetching or Creating department & service category...")
            depts_get = await client.get(
                f"{LIVE_API_BASE}/organisations/{org_id}/departments", headers=headers
            )
            existing_depts = depts_get.json() if depts_get.status_code == 200 else []
            if existing_depts:
                dept_id = existing_depts[0]["id"]
            else:
                dept_resp = await client.post(
                    f"{LIVE_API_BASE}/organisations/{org_id}/departments",
                    headers=headers,
                    json={"name": f"DevOps Infrastructure {uuid4().hex[:4]}"},
                )
                assert dept_resp.status_code == 201, f"Department creation failed: {dept_resp.text}"
                dept_id = dept_resp.json()["id"]

            cat_create = await client.post(
                f"{LIVE_API_BASE}/organisations/{org_id}/categories",
                headers=headers,
                json={
                    "department_id": dept_id,
                    "name": f"Database Infrastructure {uuid4().hex[:4]}",
                    "description": "DB connection pools & cloud servers",
                    "default_priority": "CRITICAL",
                },
            )
            assert cat_create.status_code == 201, f"Category creation failed: {cat_create.text}"
            category_id = cat_create.json()["id"]
        else:
            category_id = categories[0]["id"]
        print(f"   ✅ Service Category ID: {category_id}")

        # 4. Create Ticket (P1 Critical)
        print("\n🎫 Step 4: Submitting P1 Critical Ticket...")
        ticket_payload = {
            "category_id": category_id,
            "title": "[E2E-AUTO] Database Connection Pool Exhausted on Payment Gateway",
            "description": (
                "Payment gateway service reporting HTTP 502 errors due to asyncpg pool exhaustion. "
                "Active connections maxed out at 100/100."
            ),
            "priority": "CRITICAL",
            "source": "WEB",
        }
        create_headers = {**headers, "Idempotency-Key": str(uuid4())}
        ticket_resp = await client.post(
            f"{LIVE_API_BASE}/organisations/{org_id}/tickets",
            headers=create_headers,
            json=ticket_payload,
        )
        assert ticket_resp.status_code == 201, f"Ticket creation failed: {ticket_resp.text}"
        ticket = ticket_resp.json()
        ticket_id = ticket["id"]
        ticket_num = ticket["ticket_number"]
        print(f"   ✅ TICKET CREATED SUCCESSFULLY!")
        print(f"      • Ticket Number: {ticket_num}")
        print(f"      • Ticket ID:     {ticket_id}")
        print(f"      • Status:        {ticket['status']}")
        print(f"      • Priority:      {ticket['priority']}")
        print(f"      • Created At:    {ticket['created_at']}")

        # 5. Transition to TRIAGED
        print(f"\n⚡ Step 5: Transitioning {ticket_num} status: SUBMITTED ➔ TRIAGED...")
        trans1 = await client.post(
            f"{LIVE_API_BASE}/organisations/{org_id}/tickets/{ticket_id}/transitions",
            headers=headers,
            json={"status": "TRIAGED", "version": ticket["version"]},
        )
        assert trans1.status_code == 200, f"Transition to TRIAGED failed: {trans1.text}"
        ticket_triaged = trans1.json()
        print(
            f"   ✅ Status updated: {ticket_triaged['status']} (Version: {ticket_triaged['version']})"
        )

        # 6. Assign Ticket to User
        print(f"\n👤 Step 6: Assigning Ticket to Agent ({user_data['display_name']})...")
        assign_resp = await client.post(
            f"{LIVE_API_BASE}/organisations/{org_id}/tickets/{ticket_id}/assignment",
            headers=headers,
            json={"assigned_agent_id": user_data["id"], "version": ticket_triaged["version"]},
        )
        assert assign_resp.status_code == 200, f"Assignment failed: {assign_resp.text}"
        ticket_assigned = assign_resp.json()
        print(f"   ✅ Agent Assigned! (Version: {ticket_assigned['version']})")

        # 7. Transition to IN_PROGRESS
        print(f"\n⚙️ Step 7: Transitioning status: TRIAGED ➔ IN_PROGRESS...")
        trans2 = await client.post(
            f"{LIVE_API_BASE}/organisations/{org_id}/tickets/{ticket_id}/transitions",
            headers=headers,
            json={"status": "IN_PROGRESS", "version": ticket_assigned["version"]},
        )
        assert trans2.status_code == 200, f"Transition to IN_PROGRESS failed: {trans2.text}"
        ticket_in_prog = trans2.json()
        print(
            f"   ✅ Status updated: {ticket_in_prog['status']} (Version: {ticket_in_prog['version']})"
        )

        # 8. Add Internal Diagnostics Note
        print(f"\n💬 Step 8: Adding internal investigation note...")
        comment_resp = await client.post(
            f"{LIVE_API_BASE}/organisations/{org_id}/tickets/{ticket_id}/comments",
            headers=headers,
            json={
                "body": (
                    "[AI Copilot Diagnostics] Scaled PostgreSQL max_connections from 100 to 250. "
                    "Recycled payment gateway pods. Latency normalized to 45ms."
                ),
                "kind": "INTERNAL",
            },
        )
        print(f"   ✅ Internal note logged (Status: {comment_resp.status_code})")

        # 9. Resolve Ticket
        print(f"\n✅ Step 9: Transitioning status: IN_PROGRESS ➔ RESOLVED...")
        resolve_resp = await client.post(
            f"{LIVE_API_BASE}/organisations/{org_id}/tickets/{ticket_id}/transitions",
            headers=headers,
            json={
                "status": "RESOLVED",
                "version": ticket_in_prog["version"],
                "reason": (
                    "Increased asyncpg connection pool size to 250 and deployed patch v2.4.1. "
                    "All health checks green."
                ),
            },
        )
        assert resolve_resp.status_code == 200, f"Resolution failed: {resolve_resp.text}"
        resolved_ticket = resolve_resp.json()
        print(f"   ✅ TICKET RESOLVED SUCCESSFULLY!")
        print(f"      • Status:         {resolved_ticket['status']}")
        print(f"      • Ticket Number:  {resolved_ticket['ticket_number']}")
        print(f"      • Resolved At:    {resolved_ticket['resolved_at']}")

        # 10. Close Ticket
        print(f"\n🔒 Step 10: Transitioning status: RESOLVED ➔ CLOSED...")
        close_resp = await client.post(
            f"{LIVE_API_BASE}/organisations/{org_id}/tickets/{ticket_id}/transitions",
            headers=headers,
            json={"status": "CLOSED", "version": resolved_ticket["version"]},
        )
        assert close_resp.status_code == 200, f"Closing failed: {close_resp.text}"
        closed_ticket = close_resp.json()
        print(f"   ✅ TICKET CLOSED & ARCHIVED!")
        print(f"      • Final Status:   {closed_ticket['status']}")
        print(f"      • Closed At:      {closed_ticket['closed_at']}")

        print("\n" + "=" * 70)
        print(f"🎉 LIVE E2E TICKET CREATION & AUTOMATIC RESOLUTION TEST PASSED 100%!")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(run_e2e_ticket_flow())
