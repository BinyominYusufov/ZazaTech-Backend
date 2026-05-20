"""Smoke-test every HTTP endpoint and print a result table.

Not a pytest suite — intentionally a single-shot script you run after
starting the server with RATE_LIMIT_ENABLED=false.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass

import httpx

BASE = "http://127.0.0.1:8765"
ADMIN = ("admin@test.com", "Admin123!")
USER = ("user@test.com", "User123!")


@dataclass
class Row:
    method: str
    path: str
    expected: int
    got: int
    note: str
    body_preview: str

    @property
    def ok(self) -> bool:
        return self.got == self.expected


results: list[Row] = []


def login(email: str, password: str) -> tuple[str, str]:
    """OAuth2-form login. Returns (access, refresh)."""
    r = httpx.post(
        f"{BASE}/api/auth/login",
        data={"username": email, "password": password},
    )
    r.raise_for_status()
    body = r.json()
    return body["access"], body["refresh"]


def record(
    method: str,
    path: str,
    expected: int,
    response: httpx.Response,
    note: str,
) -> Row:
    body = response.text[:150].replace("\n", " ")
    row = Row(method, path, expected, response.status_code, note, body)
    results.append(row)
    flag = "OK" if row.ok else "FAIL"
    print(f"[{method:6}] {path:55} -> {response.status_code} {flag:4} {note}")
    return row


def call(
    method: str,
    path: str,
    expected: int,
    note: str,
    *,
    token: str | None = None,
    json_body: dict | None = None,
    data: dict | None = None,
    files: dict | None = None,
) -> httpx.Response:
    headers = {}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    r = httpx.request(
        method,
        f"{BASE}{path}",
        headers=headers,
        json=json_body,
        data=data,
        files=files,
        timeout=15.0,
    )
    record(method, path, expected, r, note)
    return r


def main() -> int:
    # ---------- Auth: get tokens ----------
    admin_access, admin_refresh = login(*ADMIN)
    user_access, user_refresh = login(*USER)

    # Confirm login also passes the "valid creds" test path.
    call("POST", "/api/auth/login", 200, "valid creds (admin)",
         data={"username": ADMIN[0], "password": ADMIN[1]})
    call("POST", "/api/auth/login", 401, "wrong password",
         data={"username": ADMIN[0], "password": "WRONG"})
    call("POST", "/api/auth/login", 401, "unknown email",
         data={"username": "nobody@test.com", "password": "x"})

    call("POST", "/api/auth/token/refresh", 200, "valid refresh",
         json_body={"refresh": user_refresh})
    call("POST", "/api/auth/token/refresh", 401, "garbage refresh",
         json_body={"refresh": "not-a-jwt"})
    call("POST", "/api/auth/token/refresh", 401, "access used as refresh",
         json_body={"refresh": user_access})
    call("POST", "/api/auth/token/refresh", 422, "missing field",
         json_body={})

    # /me
    call("GET", "/api/auth/me", 200, "with valid token", token=user_access)
    call("GET", "/api/auth/me", 401, "no token")
    call("GET", "/api/auth/me", 401, "refresh as Bearer", token=user_refresh)
    call("GET", "/api/auth/me", 401, "bad token", token="garbage.jwt.token")

    # logout
    call("POST", "/api/auth/logout", 200, "stateless logout")

    # register
    import time
    fresh_email = f"reg-{int(time.time())}@test.com"
    call("POST", "/api/auth/register", 201, "new user",
         json_body={"name": "X", "email": fresh_email, "password": "Pass1234"})
    call("POST", "/api/auth/register", 400, "duplicate email",
         json_body={"name": "X", "email": fresh_email, "password": "Pass1234"})
    call("POST", "/api/auth/register", 422, "missing password",
         json_body={"name": "X", "email": "nope@test.com"})
    call("POST", "/api/auth/register", 422, "password too short",
         json_body={"name": "X", "email": "short@test.com", "password": "abc"})

    # ---------- Meta ----------
    call("GET", "/", 200, "root")
    call("GET", "/health", 200, "health")
    call("GET", "/docs", 200, "swagger ui")
    call("GET", "/redoc", 200, "redoc")
    call("GET", "/openapi.json", 200, "openapi schema")

    # ---------- Services (public GET, auth write) ----------
    call("GET", "/api/services", 200, "list public")
    call("GET", "/api/services/999999", 404, "missing id")
    svc_create = call(
        "POST", "/api/services", 201, "create with token",
        token=user_access,
        data={
            "title": "Svc A",
            "description": "desc",
            "short_description": "s",
            "price": 100.0,
            "technologies": '["Python","FastAPI"]',
        },
    )
    svc_id = svc_create.json()["id"]
    call("POST", "/api/services", 401, "create without token",
         data={"title": "x", "description": "x", "short_description": "x", "price": 1, "technologies": "[]"})
    call("POST", "/api/services", 400, "bad technologies",
         token=user_access,
         data={"title": "x", "description": "x", "short_description": "x", "price": 1, "technologies": "not-json"})
    call("POST", "/api/services", 422, "missing title",
         token=user_access,
         data={"description": "x", "short_description": "x", "price": 1})
    call("GET", f"/api/services/{svc_id}", 200, "get by id")
    call("PUT", f"/api/services/{svc_id}", 200, "update with token",
         token=user_access, data={"title": "Svc A renamed"})
    call("PUT", "/api/services/999999", 404, "update missing",
         token=user_access, data={"title": "x"})
    call("DELETE", f"/api/services/{svc_id}", 200, "delete with token",
         token=user_access)
    call("DELETE", f"/api/services/{svc_id}", 404, "delete already gone",
         token=user_access)

    # ---------- Projects ----------
    call("GET", "/api/projects", 200, "list public")
    call("GET", "/api/projects/999999", 404, "missing id")
    prj = call(
        "POST", "/api/projects", 201, "create",
        token=user_access,
        data={
            "title": "Proj A",
            "description": "d",
            "category": "web",
            "technologies": '["Python"]',
            "featured": "false",
        },
    )
    prj_id = prj.json()["id"]
    call("POST", "/api/projects", 401, "create no token",
         data={"title": "x", "description": "x", "category": "x"})
    call("POST", "/api/projects", 400, "bad technologies json",
         token=user_access,
         data={"title": "x", "description": "x", "category": "x", "technologies": "{}"})
    call("POST", "/api/projects", 422, "missing required",
         token=user_access, data={"title": "only"})
    call("GET", f"/api/projects/{prj_id}", 200, "get by id")
    call("PUT", f"/api/projects/{prj_id}", 200, "update",
         token=user_access, data={"title": "Proj A v2"})
    call("PUT", "/api/projects/999999", 404, "update missing",
         token=user_access, data={"title": "x"})
    call("DELETE", f"/api/projects/{prj_id}", 200, "delete",
         token=user_access)
    call("DELETE", f"/api/projects/{prj_id}", 404, "delete already gone",
         token=user_access)

    # ---------- Blogs ----------
    call("GET", "/api/blogs", 200, "list public")
    call("GET", "/api/blogs/999999", 404, "missing id")
    blog = call(
        "POST", "/api/blogs", 201, "create",
        token=user_access,
        data={"title": "Blog A", "content": "c", "tags": '["a"]', "published": "true"},
    )
    blog_id = blog.json()["id"]
    call("POST", "/api/blogs", 401, "create no token",
         data={"title": "x", "content": "x"})
    call("POST", "/api/blogs", 400, "bad tags json",
         token=user_access, data={"title": "x", "content": "x", "tags": "no"})
    call("POST", "/api/blogs", 422, "missing content",
         token=user_access, data={"title": "only"})
    call("GET", f"/api/blogs/{blog_id}", 200, "get by id")
    call("PUT", f"/api/blogs/{blog_id}", 200, "update",
         token=user_access, data={"published": "false"})
    call("PUT", "/api/blogs/999999", 404, "update missing",
         token=user_access, data={"published": "false"})
    call("DELETE", f"/api/blogs/{blog_id}", 200, "delete", token=user_access)
    call("DELETE", f"/api/blogs/{blog_id}", 404, "delete already gone",
         token=user_access)

    # ---------- Contacts (POST is public; rest auth) ----------
    contact = call(
        "POST", "/api/contacts", 201, "public submit",
        json_body={"name": "X", "email": "c@e.com", "subject": "s", "message": "m"},
    )
    contact_id = contact.json()["id"]
    call("POST", "/api/contacts", 422, "missing fields",
         json_body={"name": "X"})
    call("GET", "/api/contacts", 200, "list auth", token=user_access)
    call("GET", "/api/contacts", 401, "list no token")
    call("GET", f"/api/contacts/{contact_id}", 200, "get auth",
         token=user_access)
    call("GET", "/api/contacts/999999", 404, "get missing",
         token=user_access)
    call("PUT", f"/api/contacts/{contact_id}/read", 200, "mark read",
         token=user_access)
    call("PUT", "/api/contacts/999999/read", 404, "mark missing",
         token=user_access)
    call("DELETE", f"/api/contacts/{contact_id}", 200, "delete auth",
         token=user_access)
    call("DELETE", f"/api/contacts/{contact_id}", 404, "delete already gone",
         token=user_access)

    # ---------- Dashboard ----------
    call("GET", "/api/dashboard/stats", 200, "stats auth", token=user_access)
    call("GET", "/api/dashboard/stats", 401, "stats no token")

    # ---------- Users (super_admin only) ----------
    call("GET", "/api/users", 200, "list as admin", token=admin_access)
    call("GET", "/api/users", 401, "list no token")
    call("GET", "/api/users", 403, "list as editor", token=user_access)
    new_user = call(
        "POST", "/api/users", 201, "create as admin",
        token=admin_access,
        data={"name": "U", "email": f"u-{int(time.time())}@t.com",
              "password": "Pass1234", "role": "editor"},
    )
    new_user_id = new_user.json()["id"]
    call("POST", "/api/users", 401, "create no token",
         data={"name": "x", "email": "y@y.com", "password": "Pass1234", "role": "editor"})
    call("POST", "/api/users", 403, "create as editor",
         token=user_access,
         data={"name": "x", "email": "y2@y.com", "password": "Pass1234", "role": "editor"})
    call("POST", "/api/users", 400, "invalid role",
         token=admin_access,
         data={"name": "x", "email": "y3@y.com", "password": "Pass1234", "role": "alien"})
    call("GET", f"/api/users/{new_user_id}", 200, "get by id",
         token=admin_access)
    call("GET", "/api/users/999999", 404, "get missing",
         token=admin_access)
    call("PUT", f"/api/users/{new_user_id}", 200, "update",
         token=admin_access, data={"name": "U2"})
    call("PUT", "/api/users/999999", 404, "update missing",
         token=admin_access, data={"name": "x"})
    call("DELETE", f"/api/users/{new_user_id}", 200, "delete",
         token=admin_access)
    call("DELETE", f"/api/users/{new_user_id}", 404, "delete already gone",
         token=admin_access)

    # ---------- Ambassador-applications (public POST) ----------
    appl_email = f"appl-{int(time.time())}@t.com"
    appl = call(
        "POST", "/api/ambassador-applications", 201, "public submit",
        json_body={"full_name": "A", "email": appl_email, "phone": "1", "profession": "p"},
    )
    appl_id = appl.json()["data"]["id"]
    call("POST", "/api/ambassador-applications", 400, "duplicate pending",
         json_body={"full_name": "A", "email": appl_email, "phone": "1", "profession": "p"})
    call("POST", "/api/ambassador-applications", 422, "missing fields",
         json_body={"full_name": "A"})

    # ---------- Admin ambassador-applications ----------
    call("GET", "/api/admin/ambassador-applications", 200, "list",
         token=admin_access)
    call("GET", "/api/admin/ambassador-applications", 401, "no token")
    call("GET", "/api/admin/ambassador-applications", 403, "as editor",
         token=user_access)
    call("GET", f"/api/admin/ambassador-applications/{appl_id}", 200,
         "get one", token=admin_access)
    call("GET", "/api/admin/ambassador-applications/999999", 404,
         "missing", token=admin_access)
    call("PATCH", f"/api/admin/ambassador-applications/{appl_id}/approve",
         200, "approve", token=admin_access)
    call("PATCH", f"/api/admin/ambassador-applications/{appl_id}/approve",
         400, "already reviewed", token=admin_access)

    # second app for reject flow
    appl2 = httpx.post(
        f"{BASE}/api/ambassador-applications",
        json={"full_name": "B", "email": f"rej-{int(time.time())}@t.com",
              "phone": "1", "profession": "p"},
    ).json()
    appl2_id = appl2["data"]["id"]
    call("PATCH", f"/api/admin/ambassador-applications/{appl2_id}/reject",
         200, "reject", token=admin_access)
    call("PATCH", "/api/admin/ambassador-applications/999999/reject",
         404, "reject missing", token=admin_access)

    # ---------- Public ambassadors ----------
    call("GET", "/api/ambassadors", 200, "list public")
    call("GET", "/api/ambassadors/999999", 404, "missing")

    # ---------- Admin ambassadors ----------
    call("GET", "/api/admin/ambassadors", 200, "list admin",
         token=admin_access)
    call("GET", "/api/admin/ambassadors", 401, "no token")
    call("GET", "/api/admin/ambassadors", 403, "as editor",
         token=user_access)
    amb = call(
        "POST", "/api/admin/ambassadors", 201, "create",
        token=admin_access, data={"name": "Amb A", "role": "lead"},
    )
    amb_id = amb.json()["data"]["id"]
    call("POST", "/api/admin/ambassadors", 401, "create no token",
         data={"name": "x", "role": "y"})
    call("POST", "/api/admin/ambassadors", 403, "create as editor",
         token=user_access, data={"name": "x", "role": "y"})
    call("POST", "/api/admin/ambassadors", 422, "missing fields",
         token=admin_access, data={"name": "only"})
    call("GET", f"/api/admin/ambassadors/{amb_id}", 200, "get",
         token=admin_access)
    call("GET", "/api/admin/ambassadors/999999", 404, "missing",
         token=admin_access)
    call("PATCH", f"/api/admin/ambassadors/{amb_id}", 200, "update",
         token=admin_access, data={"role": "captain"})
    call("PATCH", f"/api/admin/ambassadors/{amb_id}/toggle-active", 200,
         "toggle active", token=admin_access)
    call("PATCH", f"/api/admin/ambassadors/{amb_id}/toggle-featured", 200,
         "toggle featured", token=admin_access)
    # Now also exists in public list when active again
    call("PATCH", f"/api/admin/ambassadors/{amb_id}/toggle-active", 200,
         "toggle active back", token=admin_access)
    call("GET", f"/api/ambassadors/{amb_id}", 200, "public get visible",
         )
    call("DELETE", f"/api/admin/ambassadors/{amb_id}", 200, "delete",
         token=admin_access)
    call("DELETE", f"/api/admin/ambassadors/{amb_id}", 404, "delete gone",
         token=admin_access)

    # ---------- Report ----------
    print("\n\n=== REPORT ===")
    print(f"{'Method':6} | {'Endpoint':55} | {'Expected':8} | {'Got':3} | {'Status':6} | Note")
    print("-" * 130)
    ok = fail = 0
    for r in results:
        flag = "OK" if r.ok else "FAIL"
        if r.ok:
            ok += 1
        else:
            fail += 1
        print(f"{r.method:6} | {r.path:55} | {r.expected:8} | {r.got:3} | {flag:6} | {r.note}")
    print(f"\nTotal: {ok} OK / {fail} FAIL  (of {len(results)})")

    if fail:
        print("\n=== FAILURES ===")
        for r in results:
            if not r.ok:
                print(f"  [{r.method}] {r.path} -> expected {r.expected}, got {r.got}")
                print(f"     note: {r.note}")
                print(f"     body: {r.body_preview}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
