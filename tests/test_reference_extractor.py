from hallucheck.reference_extractor import extract_references


def test_extract_method_call():
    refs = extract_references("    perms = user.get_permissions()")
    assert len(refs) == 1
    assert refs[0]["kind"] == "method"
    assert refs[0]["name"] == "get_permissions"
    assert refs[0]["full_name"] == "user.get_permissions"


def test_extract_import():
    refs = extract_references("    from utils.crypto import sign_payload")
    assert len(refs) == 1
    assert refs[0]["kind"] == "import"
    assert refs[0]["name"] == "sign_payload"
    assert refs[0]["module"] == "utils.crypto"


def test_extract_type_annotation():
    refs = extract_references("    response: AuthResponse = process(data)")

    # It might extract both the type and the function call
    type_refs = [r for r in refs if r["kind"] == "type"]
    assert len(type_refs) == 1
    assert type_refs[0]["name"] == "AuthResponse"

    func_refs = [r for r in refs if r["kind"] == "function"]
    assert len(func_refs) == 1
    assert func_refs[0]["name"] == "process"
