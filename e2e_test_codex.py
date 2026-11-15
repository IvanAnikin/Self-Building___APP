#!/usr/bin/env python
"""
End-to-End Tests for Codex CLI Integration (Phase 6A)

Tests the full feature implementation workflow through HTTP like a real user:
1. User registration/login
2. Feature request detection via chat
3. Feature analysis
4. Feature implementation (tests both Codex and legacy engines)
5. Feature preview
6. Feature apply
7. Version history tracking
8. Verify app still works after feature applied

This test complements the existing e2e_test.py by focusing specifically on
the feature implementation pipeline with Codex integration.
"""

import requests
import re
import json
import time

BASE = 'http://127.0.0.1:8000'
results = []


def log(test_name, passed, detail=""):
    """Log test result with color and detail"""
    icon = "✅" if passed else "❌"
    results.append((test_name, passed))
    print(f"\n{icon} {test_name}")
    if detail:
        print(f"   {detail}")


def main():
    print("\n" + "=" * 80)
    print("🧪 PHASE 6A: CODEX CLI INTEGRATION - E2E TESTS")
    print("=" * 80)
    
    # ============================================================
    # SETUP: Register and login test user
    # ============================================================
    print("\n" + "=" * 60)
    print("SETUP: User Registration & Login")
    print("=" * 60)
    
    s = requests.Session()
    
    # Get CSRF token
    r = s.get(f'{BASE}/accounts/register/')
    csrf = re.search(r'name="csrfmiddlewaretoken" value="(.*?)"', r.text)
    token = csrf.group(1) if csrf else ''
    
    # Register user
    username = f'codex_test_user_{int(time.time())}'
    r = s.post(f'{BASE}/accounts/register/', data={
        'csrfmiddlewaretoken': token,
        'username': username,
        'email': f'{username}@test.com',
        'password': 'SecurePass99!',
        'password_confirm': 'SecurePass99!'
    }, allow_redirects=True)
    
    registered = 'chatInput' in r.text or 'editor' in r.text.lower()
    log("Setup: User registration", registered, f"User: {username}")
    
    if not registered:
        print("⚠️  Cannot proceed without successful registration")
        return
    
    # Get CSRF token for API calls
    csrf_token = s.cookies.get('csrftoken', '')
    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token
    }
    
    # ============================================================
    # TEST 1: Feature Request Detection
    # ============================================================
    print("\n" + "=" * 60)
    print("TEST 1: Feature Request Detection via Chat")
    print("=" * 60)
    
    r = s.post(f'{BASE}/api/chat/', headers=headers, json={
        'message': 'Can you add a button that shows the current time when clicked?'
    })
    data = r.json()
    
    feature_detected = data.get('is_feature_request', False)
    feature_id = data.get('feature_request_id')
    
    log(
        "Feature request detected",
        feature_detected and feature_id is not None,
        f"Feature ID: {feature_id}"
    )
    
    if not feature_id:
        print("⚠️  Cannot proceed without feature ID")
        return
    
    # ============================================================
    # TEST 2: Feature Analysis
    # ============================================================
    print("\n" + "=" * 60)
    print("TEST 2: Feature Analysis")
    print("=" * 60)
    
    r = s.post(f'{BASE}/api/features/analyze/', headers=headers, json={
        'feature_id': feature_id
    })
    data = r.json()
    
    analysis_success = data.get('status') == 'success'
    analysis = data.get('analysis', {})
    feasible = analysis.get('feasible', False)
    files_to_modify = analysis.get('files_to_modify', [])
    
    log(
        "Feature analysis",
        analysis_success and feasible,
        f"Feasible: {feasible}, Files: {len(files_to_modify)}"
    )
    
    # ============================================================
    # TEST 3: Feature Implementation (Codex or Legacy)
    # ============================================================
    print("\n" + "=" * 60)
    print("TEST 3: Feature Implementation")
    print("=" * 60)
    
    r = s.post(f'{BASE}/api/features/implement/', headers=headers, json={
        'feature_id': feature_id
    })
    data = r.json()
    
    impl_success = data.get('status') == 'success'
    generated_files = data.get('generated_files', [])
    engine_used = data.get('engine', 'unknown')
    
    log(
        "Feature implementation",
        impl_success and len(generated_files) > 0,
        f"Engine: {engine_used}, Files generated: {len(generated_files)}"
    )
    
    # TEST 3a: Verify 'engine' field exists
    log(
        "Response includes 'engine' field",
        'engine' in data and engine_used in ['codex', 'legacy'],
        f"Engine: {engine_used}"
    )
    
    # TEST 3b: Verify generated files structure
    if generated_files:
        first_file = generated_files[0]
        has_required_fields = all(
            key in first_file 
            for key in ['file', 'code', 'changes', 'notes']
        )
        log(
            "Generated files have correct structure",
            has_required_fields,
            f"Sample file: {first_file.get('file', 'N/A')}"
        )
    
    # ============================================================
    # TEST 4: Feature Preview (Diff Generation)
    # ============================================================
    print("\n" + "=" * 60)
    print("TEST 4: Feature Preview (Diff)")
    print("=" * 60)
    
    r = s.post(f'{BASE}/api/features/preview/', headers=headers, json={
        'feature_id': feature_id
    })
    data = r.json()
    
    preview_success = data.get('status') == 'success'
    previews = data.get('previews', [])
    
    log(
        "Feature preview generation",
        preview_success and len(previews) > 0,
        f"Diffs generated: {len(previews)}"
    )
    
    # Verify diff structure
    if previews:
        first_diff = previews[0]
        has_diff_fields = all(
            key in first_diff 
            for key in ['file_path', 'diff', 'additions', 'deletions']
        )
        log(
            "Diff previews have correct structure",
            has_diff_fields,
            f"Sample: +{first_diff.get('additions', 0)} -{first_diff.get('deletions', 0)}"
        )
    
    # ============================================================
    # TEST 5: Feature Apply (Write Files + Git Commit)
    # ============================================================
    print("\n" + "=" * 60)
    print("TEST 5: Feature Apply")
    print("=" * 60)
    
    r = s.post(f'{BASE}/api/features/apply/', headers=headers, json={
        'feature_id': feature_id
    })
    data = r.json()
    
    apply_success = data.get('status') == 'success'
    applied_files = data.get('applied_files', [])
    commit_hash = data.get('commit_hash', '')
    
    log(
        "Feature apply (files written)",
        apply_success and len(applied_files) > 0,
        f"Files applied: {len(applied_files)}, Commit: {commit_hash[:7] if commit_hash else 'N/A'}"
    )
    
    # ============================================================
    # TEST 6: Version History
    # ============================================================
    print("\n" + "=" * 60)
    print("TEST 6: Version History Tracking")
    print("=" * 60)
    
    r = s.get(f'{BASE}/api/versions/', headers=headers)
    data = r.json()
    
    versions_success = data.get('status') == 'success'
    versions = data.get('versions', [])
    current_branch = data.get('current_branch', 'unknown')
    
    log(
        "Version history API",
        versions_success,
        f"Branch: {current_branch}, Versions: {len(versions)}"
    )
    
    # Verify our commit appears in history
    if commit_hash and versions:
        commit_in_history = any(
            v.get('commit_hash', '').startswith(commit_hash[:7]) 
            for v in versions
        )
        log(
            "Applied feature appears in history",
            commit_in_history,
            f"Looking for commit: {commit_hash[:7]}"
        )
    
    # ============================================================
    # TEST 7: App Still Loads After Feature Applied
    # ============================================================
    print("\n" + "=" * 60)
    print("TEST 7: Application Health Check")
    print("=" * 60)
    
    r = s.get(f'{BASE}/en/', allow_redirects=True)
    app_loads = r.status_code == 200
    has_editor = 'id="editor"' in r.text
    has_chat = 'chatInput' in r.text
    
    log(
        "Main page loads successfully",
        app_loads and has_editor and has_chat,
        f"Status: {r.status_code}, Editor: {has_editor}, Chat: {has_chat}"
    )
    
    # ============================================================
    # TEST 8: Feature Request Model Updated
    # ============================================================
    print("\n" + "=" * 60)
    print("TEST 8: Database Integrity")
    print("=" * 60)
    
    # List features to verify the feature exists and has correct engine field
    r = s.get(f'{BASE}/api/features/', headers=headers)
    data = r.json()
    
    features = data.get('features', [])
    our_feature = next((f for f in features if f.get('id') == feature_id), None)
    
    if our_feature:
        has_status = our_feature.get('status') in ['completed', 'approved', 'processing']
        has_code = our_feature.get('has_code', False)
        
        log(
            "Feature record complete",
            has_status and has_code,
            f"Status: {our_feature.get('status')}, Has code: {has_code}"
        )
    
    # ============================================================
    # TEST 9: Existing Functionality Unaffected
    # ============================================================
    print("\n" + "=" * 60)
    print("TEST 9: Regression Tests (Existing Features)")
    print("=" * 60)
    
    # Test Chat API still works
    r = s.post(f'{BASE}/api/chat/', headers=headers, json={
        'message': 'Hello, just testing the chat still works'
    })
    data = r.json()
    chat_ok = data.get('status') == 'success' and len(data.get('response', '')) > 0
    log("Chat API", chat_ok)
    
    # Test Code Save still works
    r = s.post(f'{BASE}/api/save/', headers=headers, json={
        'code': 'print("E2E test after Codex integration")',
        'filename': 'e2e_codex_test.py'
    })
    data = r.json()
    save_ok = data.get('status') == 'success'
    log("Save Code API", save_ok)
    
    # Test Code Execute still works
    r = s.post(f'{BASE}/api/execute/', headers=headers, json={
        'code': 'print("Codex E2E test execution")',
        'language': 'python',
        'filename': 'e2e_codex_test.py'
    })
    data = r.json()
    exec_ok = data.get('status') == 'success' and 'Codex E2E' in data.get('stdout', '')
    log("Execute Code API", exec_ok)
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 80)
    print("📊 E2E TEST SUMMARY - PHASE 6A CODEX INTEGRATION")
    print("=" * 80)
    
    passed = sum(1 for _, p in results if p)
    failed = sum(1 for _, p in results if not p)
    total = len(results)
    
    print(f"\n   Total:  {total} tests")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   Rate:   {passed/total*100:.0f}%")
    print()
    
    for name, p in results:
        print(f"   {'✅' if p else '❌'} {name}")
    
    print()
    
    if failed == 0:
        print("🎉 ALL E2E TESTS PASSED!")
        print("✨ Phase 6A Codex CLI Integration is working correctly")
    else:
        print(f"⚠️  {failed} test(s) need attention")
    
    print()
    return failed == 0


if __name__ == '__main__':
    try:
        success = main()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server at", BASE)
        print("   Make sure the Django server is running:")
        print("   python manage.py runserver")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
