#!/usr/bin/env python3
"""
模块一简单测试脚本 - 验证核心功能
"""
import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.db.session import Base, engine, SessionLocal as TestingSessionLocal
from src.models.user import User
from src.core.security import get_password_hash, verify_password
from src.core.security import create_access_token, create_refresh_token

def test_password_security():
    """测试密码加密与验证"""
    print("🔐 测试密码安全功能...")
    password = "TestPassword123"
    hash_result = get_password_hash(password)
    assert hash_result != password, "密码应该被加密"
    assert verify_password(password, hash_result), "密码验证应该通过"
    assert not verify_password("WrongPassword", hash_result), "错误密码应该验证失败"
    print("✅ 密码安全测试通过")
    return True

def test_jwt_tokens():
    """测试JWT令牌生成"""
    print("🎫 测试JWT令牌功能...")
    user_id = 123
    access_token, _ = create_access_token(data={"sub": str(user_id)})
    refresh_token, _ = create_refresh_token(data={"sub": str(user_id)})
    assert access_token is not None, "Access token 应该生成"
    assert refresh_token is not None, "Refresh token 应该生成"
    assert access_token != refresh_token, "两个token应该不同"
    print(f"✅ JWT令牌测试通过")
    print(f"   Access Token: {access_token[:30]}...")
    print(f"   Refresh Token: {refresh_token[:30]}...")
    return True

def test_database_models():
    """测试数据库模型"""
    print("🗄️ 测试数据库模型...")
    try:
        # 创建测试表
        Base.metadata.create_all(bind=engine)

        # 测试创建用户
        db = TestingSessionLocal()
        test_email = "test_module_one@example.com"

        # 清理可能存在的测试数据
        existing = db.query(User).filter(User.email == test_email).first()
        if existing:
            db.delete(existing)
            db.commit()

        # 创建新用户
        user = User(
            email=test_email,
            password_hash=get_password_hash("TestPassword123"),
            nickname="测试用户",
            status=1
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        assert user.id is not None, "用户ID应该被自动生成"
        assert user.email == test_email, "邮箱应该匹配"
        assert user.nickname == "测试用户", "昵称应该匹配"

        print(f"✅ 数据库模型测试通过")
        print(f"   测试用户ID: {user.id}")

        # 清理
        db.delete(user)
        db.commit()
        db.close()

        return True
    except Exception as e:
        print(f"❌ 数据库模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("🚀 模块一（用户与权限子模块）简单测试")
    print("=" * 60)

    tests = [
        ("密码安全功能", test_password_security),
        ("JWT令牌功能", test_jwt_tokens),
        ("数据库模型", test_database_models),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {name}测试异常: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        print()

    print("=" * 60)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
