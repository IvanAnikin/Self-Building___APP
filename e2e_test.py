"""End-to-end test suite for Self-Building App Phase 5"""
import requests
import re
import json
import sys

BASE = 'http://127.0.0.1:8000'
results = []

def log(test_name, passed, detail=""):
    icon = "✅" if passed else "❌"
    results.append((test_name, passed))
    print(f"\n{icon} {test_name}")
    if detail:
        print(f"   {detail}")

# ============================================================
# TEST 1: Registration
# ============================================================
print("=" * 60)
print("TEST 1: User Registration")
print("=" * 60)
s = requests.Session()
r = s.get(f'{BASE}/accounts/register/')
csrf = re.search(r'name="csrfmiddlewaretoken" value="(.*?)"', r.text)
token = csrf.group(1) if csrf else ''

r = s.post(f'{BASE}/accounts/register/', data={
    'csrfmiddlewaretoken': token,
    'username': 'testuser_e2e',
    'email': 'test@e2e.com',
    'password': 'SecurePass99!',
    'password_confirm': 'SecurePass99!'
}, allow_redirects=True)

registered = 'chatInput' in r.text or 'editor' in r.text.lower()
if not registered and 'already exists' in r.text:
    print("   User already exists, will test login instead")
    log("Registration (user exists)", True, "User was already created previously")
else:
    log("Registration", registered, f"Status: {r.status_code}, redirected to editor: {registered}")

# ============================================================
# TEST 2: Logout
# ============================================================
print("\n" + "=" * 60)
print("TEST 2: Logout")
print("=" * 60)
r = s.get(f'{BASE}/accounts/logout/', allow_redirects=True)
at_login = 'login' in r.url or 'Login' in r.text
log("Logout", at_login, f"Redirected to: {r.url}")

# ============================================================
# TEST 3: Login
# ============================================================
print("\n" + "=" * 60)
print("TEST 3: Login")
print("=" * 60)
s2 = requests.Session()
r = s2.get(f'{BASE}/accounts/login/')
csrf = re.search(r'name="csrfmiddlewaretoken" value="(.*?)"', r.text)
token = csrf.group(1) if csrf else ''

r = s2.post(f'{BASE}/accounts/login/', data={
    'csrfmiddlewaretoken': token,
    'username': 'testuser_e2e',
    'password': 'SecurePass99!'
}, allow_redirects=True)

logged_in = 'chatInput' in r.text or 'editor' in r.text.lower()
log("Login", logged_in, f"Status: {r.status_code}, at editor: {logged_in}")

# Get fresh CSRF for API calls
csrf_token = s2.cookies.get('csrftoken', '')
headers = {
    'Content-Type': 'application/json',
    'X-CSRFToken': csrf_token
}

# ============================================================
# TEST 4: Main page loads (authenticated)
# ============================================================
print("\n" + "=" * 60)
print("TEST 4: Main Page Content")
print("=" * 60)
r = s2.get(f'{BASE}/en/')
has_editor = 'id="editor"' in r.text
has_chat = 'chatInput' in r.text
has_user = 'testuser_e2e' in r.text
has_logout = 'logout' in r.text.lower()
log("Editor present", has_editor)
log("Chat input present", has_chat)
log("Username displayed", has_user)
log("Logout button present", has_logout)

# ============================================================
# TEST 5: Chat API
# ============================================================
print("\n" + "=" * 60)
print("TEST 5: Chat API")
print("=" * 60)
r = s2.post(f'{BASE}/api/chat/', headers=headers, json={
    'message': 'Hello, this is an E2E test!'
})
data = r.json()
chat_ok = data.get('status') == 'success' and len(data.get('response', '')) > 0
log("Chat API", chat_ok, f"Status: {data.get('status')}, response length: {len(data.get('response', ''))}")

# ============================================================
# TEST 6: Save Code API
# ============================================================
print("\n" + "=" * 60)
print("TEST 6: Save Code API")
print("=" * 60)
r = s2.post(f'{BASE}/api/save/', headers=headers, json={
    'code': 'print("Hello from E2E test!")',
    'filename': 'e2e_test.py'
})
data = r.json()
save_ok = data.get('status') == 'success'
log("Save Code API", save_ok, f"Response: {data}")

# ============================================================
# TEST 7: Execute Code API
# ============================================================
print("\n" + "=" * 60)
print("TEST 7: Execute Code API")
print("=" * 60)
r = s2.post(f'{BASE}/api/execute/', headers=headers, json={
    'code': 'print("E2E test execution works!")',
    'language': 'python',
    'filename': 'e2e_test.py'
})
data = r.json()
exec_ok = data.get('status') == 'success' and 'E2E test execution works!' in data.get('stdout', '')
log("Execute Code API", exec_ok, f"stdout: {data.get('stdout', '').strip()}")

# ============================================================
# TEST 8: Feature Request Detection (via chat)
# ============================================================
print("\n" + "=" * 60)
print("TEST 8: Feature Request Detection")
print("=" * 60)
r = s2.post(f'{BASE}/api/chat/', headers=headers, json={
    'message': 'Can you add a dark mode toggle button to the interface?'
})
data = r.json()
feat_detected = data.get('is_feature_request', False)
feat_id = data.get('feature_id')
log("Feature detected in chat", feat_detected or feat_id is not None, f"Feature ID: {feat_id}, detected: {feat_detected}")

# ============================================================
# TEST 9: List Features API
# ============================================================
print("\n" + "=" * 60)
print("TEST 9: List Features API")
print("=" * 60)
r = s2.get(f'{BASE}/api/features/', headers=headers)
data = r.json()
features_ok = data.get('status') == 'success'
feature_count = len(data.get('features', []))
log("List Features API", features_ok, f"Found {feature_count} feature(s)")

# ============================================================
# TEST 10: Version History API
# ============================================================
print("\n" + "=" * 60)
print("TEST 10: Version History API")
print("=" * 60)
r = s2.get(f'{BASE}/api/versions/', headers=headers)
data = r.json()
versions_ok = data.get('status') == 'success'
version_count = len(data.get('versions', []))
branch = data.get('current_branch', 'unknown')
log("Version History API", versions_ok, f"Branch: {branch}, versions: {version_count}")

# ============================================================
# TEST 11: User Isolation (second user sees no data)
# ============================================================
print("\n" + "=" * 60)
print("TEST 11: User Isolation")
print("=" * 60)
s3 = requests.Session()
r = s3.get(f'{BASE}/accounts/register/')
csrf = re.search(r'name="csrfmiddlewaretoken" value="(.*?)"', r.text)
token = csrf.group(1) if csrf else ''

r = s3.post(f'{BASE}/accounts/register/', data={
    'csrfmiddlewaretoken': token,
    'username': 'testuser_e2e_2',
    'email': 'test2@e2e.com',
    'password': 'SecurePass99!',
    'password_confirm': 'SecurePass99!'
}, allow_redirects=True)

# Handle case where user already exists - login instead
if 'already exists' in r.text:
    csrf = re.search(r'name="csrfmiddlewaretoken" value="(.*?)"', r.text)
    token = csrf.group(1) if csrf else ''
    r = s3.get(f'{BASE}/accounts/login/')
    csrf = re.search(r'name="csrfmiddlewaretoken" value="(.*?)"', r.text)
    token = csrf.group(1) if csrf else ''
    r = s3.post(f'{BASE}/accounts/login/', data={
        'csrfmiddlewaretoken': token,
        'username': 'testuser_e2e_2',
        'password': 'SecurePass99!'
    }, allow_redirects=True)

csrf2 = s3.cookies.get('csrftoken', '')
headers2 = {'Content-Type': 'application/json', 'X-CSRFToken': csrf2}

# User 2 should see 0 features
r = s3.get(f'{BASE}/api/features/', headers=headers2)
data = r.json()
user2_features = len(data.get('features', []))
isolated = user2_features == 0
log("User isolation (features)", isolated, f"User 2 sees {user2_features} features (expected 0)")

# ============================================================
# TEST 12: Unauthenticated access blocked
# ============================================================
print("\n" + "=" * 60)
print("TEST 12: Auth Protection")
print("=" * 60)
s4 = requests.Session()
r = s4.get(f'{BASE}/en/', allow_redirects=False)
blocked = r.status_code == 302 and 'login' in r.headers.get('Location', '')
log("Unauthenticated redirect to login", blocked, f"Status: {r.status_code}, Location: {r.headers.get('Location', 'n/a')}")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("📊 E2E TEST SUMMARY")
print("=" * 60)
passed_count = sum(1 for _, p in results if p)
failed_count = sum(1 for _, p in results if not p)
print(f"\n   Total:  {len(results)} tests")
print(f"   ✅ Passed: {passed_count}")
print(f"   ❌ Failed: {failed_count}")
print(f"   Rate:   {passed_count/len(results)*100:.0f}%")
print()
for name, p in results:
    print(f"   {'✅' if p else '❌'} {name}")
print()
if failed_count == 0:
    print("🎉 ALL TESTS PASSED!")
else:
    print(f"⚠️  {failed_count} test(s) need attention")

sys.exit(0 if failed_count == 0 else 1)
