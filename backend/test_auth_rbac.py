import requests

BASE = "http://127.0.0.1:8000/api"

# 1. Admin login
r_admin = requests.post(f"{BASE}/auth/login", json={"username_or_email": "admin@bsrhub.lk", "password": "Admin@123456"})
assert r_admin.status_code == 200, f"Admin login failed: {r_admin.text}"
admin_token = r_admin.json()["access_token"]
print("✓ Admin login successful (JWT token issued)")

# 2. Admin get users
r_users = requests.get(f"{BASE}/users", headers={"Authorization": f"Bearer {admin_token}"})
assert r_users.status_code == 200, f"Admin get users failed: {r_users.text}"
users = r_users.json()
print(f"✓ Admin fetched {len(users)} user accounts")

# 3. Viewer login
r_viewer = requests.post(f"{BASE}/auth/login", json={"username_or_email": "viewer@bsrhub.lk", "password": "Viewer@123456"})
assert r_viewer.status_code == 200, f"Viewer login failed: {r_viewer.text}"
viewer_token = r_viewer.json()["access_token"]
print("✓ Viewer login successful")

# 4. Viewer RBAC test - cannot access user management
r_viewer_users = requests.get(f"{BASE}/users", headers={"Authorization": f"Bearer {viewer_token}"})
assert r_viewer_users.status_code == 403, f"Expected 403 for viewer, got {r_viewer_users.status_code}"
print(f"✓ RBAC check 1: Viewer blocked from /api/users with HTTP {r_viewer_users.status_code}")

# 5. Viewer RBAC test - cannot delete documents
r_del = requests.delete(f"{BASE}/documents/99999", headers={"Authorization": f"Bearer {viewer_token}"})
assert r_del.status_code == 403, f"Expected 403 for viewer delete, got {r_del.status_code}"
print(f"✓ RBAC check 2: Viewer blocked from document deletion with HTTP {r_del.status_code}")

# 6. Audit Trail test
r_audit = requests.get(f"{BASE}/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
assert r_audit.status_code == 200, f"Audit logs failed: {r_audit.text}"
audit_logs = r_audit.json()
print(f"✓ Audit Trail verified: {len(audit_logs)} security events recorded")

# 7. Rates query test
r_rates = requests.get(f"{BASE}/rates/search?limit=5", headers={"Authorization": f"Bearer {admin_token}"})
assert r_rates.status_code == 200, f"Rates search failed: {r_rates.text}"
total_rates = r_rates.json()["total"]
print(f"✓ Rates catalog verified: {total_rates} items intact and searchable")

print("\n==============================================")
print("ALL CENTRALIZED SECURITY & RBAC TESTS PASSED!")
print("==============================================")
