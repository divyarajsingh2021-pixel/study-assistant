from app.services.auth_service import auth_service


def test_auth_service_initialization_and_login():
    user = auth_service.authenticate_user("admin", "admin123")
    assert user is not None
    assert user["role"] == "Admin"
    assert user["token"].startswith("dsc_tok_")


def test_auth_service_invalid_login():
    user = auth_service.authenticate_user("admin", "wrong_password")
    assert user is None


def test_token_validation():
    user = auth_service.authenticate_user("student1", "study123")
    assert user is not None
    token = user["token"]

    validated = auth_service.get_user_from_token(f"Bearer {token}")
    assert validated is not None
    assert validated["username"] == "student1"


def test_change_password():
    success = auth_service.change_password("student1", "study123", "newpassword123")
    assert success is True

    # Check new password works
    user = auth_service.authenticate_user("student1", "newpassword123")
    assert user is not None

    # Check old password fails
    assert auth_service.authenticate_user("student1", "study123") is None


def test_forgot_password_recovery():
    # Alex Turner recovery_code is STUDENT1
    success = auth_service.forgot_password_recovery("student1", "STUDENT1", "recoveredpass")
    assert success is True
    assert auth_service.authenticate_user("student1", "recoveredpass") is not None


def test_register_and_delete_user():
    new_user = auth_service.register_user(
        username="newstudent",
        password="password123",
        name="New Student",
        email="new@studyassistant.ai",
        role="Student",
        recovery_code="NEWCODE",
    )
    assert new_user["username"] == "newstudent"

    all_users = auth_service.get_all_users(is_admin=True)
    assert any(u["username"] == "newstudent" for u in all_users)

    auth_service.delete_user("newstudent")
    all_users_after = auth_service.get_all_users(is_admin=True)
    assert not any(u["username"] == "newstudent" for u in all_users_after)
