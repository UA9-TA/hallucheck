import pytest
from hallucheck.diff_parser import parse_patch_content

def test_parse_patch_content():
    patch_content = """--- a/example.py
+++ b/example.py
@@ -1,5 +1,8 @@
 def process_login(user, data):
-    return LoginResponse(token="abc", user_id=1)
+    from utils.crypto import sign_payload
+    perms = user.get_permissions()
+    token = sign_payload(data)
+    response: AuthResponse = AuthResponse(token=token, user_id=user.id)
+    return response
"""
    diff_lines = parse_patch_content(patch_content)

    assert len(diff_lines) == 5
    assert diff_lines[0].file == "example.py"
    assert diff_lines[0].line_number == 2
    assert diff_lines[0].content == "    from utils.crypto import sign_payload"

    assert diff_lines[1].line_number == 3
    assert diff_lines[1].content == "    perms = user.get_permissions()"

    assert diff_lines[2].line_number == 4
    assert diff_lines[3].line_number == 5
    assert diff_lines[4].line_number == 6
