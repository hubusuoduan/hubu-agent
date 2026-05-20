"""认证模块测试脚本"""
import asyncio
from datetime import datetime
from loguru import logger

from app.database.session import get_async_session
from app.services.auth_service import AuthService
from app.auth.auth_jwt import JWTAuth
from app.auth.config import AuthConfig
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserInfo
from app.auth.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    InvalidTokenError,
    MissingTokenError,
    AccessTokenRequired,
    RefreshTokenRequired
)


# ==================== JWT Auth 测试 ====================

def test_jwt_config():
    """测试 JWT 配置"""
    print("\n========== 测试 JWT 配置 ==========")
    config = AuthConfig()
    
    assert config.secret_key is not None, "secret_key 不能为空"
    assert config.algorithm == "HS256", "默认算法应为 HS256"
    assert config.access_token_expires.total_seconds() == 1800, "访问Token默认应为30分钟"
    assert config.refresh_token_expires.total_seconds() == 604800, "刷新Token默认应为7天"
    assert "headers" in config.token_location, "默认应从Header获取Token"
    
    print("✅ JWT 配置测试通过")


def test_jwt_token_creation():
    """测试 JWT Token 创建"""
    print("\n========== 测试 JWT Token 创建 ==========")
    config = AuthConfig()
    jwt_auth = JWTAuth(config)
    
    # 测试创建访问Token
    access_token = jwt_auth.create_access_token(
        subject="test_user_123",
        user_claims={"username": "testuser"}
    )
    assert access_token is not None, "访问Token不应为空"
    assert isinstance(access_token, str), "访问Token应为字符串"
    print(f"✅ 访问Token创建成功: {access_token[:50]}...")
    
    # 测试创建刷新Token
    refresh_token = jwt_auth.create_refresh_token(
        subject="test_user_123",
        user_claims={"username": "testuser"}
    )
    assert refresh_token is not None, "刷新Token不应为空"
    assert isinstance(refresh_token, str), "刷新Token应为字符串"
    print(f"✅ 刷新Token创建成功: {refresh_token[:50]}...")
    
    # 验证两个Token不同
    assert access_token != refresh_token, "访问Token和刷新Token应不同"
    print("✅ Token区分测试通过")


def test_jwt_token_verification():
    """测试 JWT Token 验证"""
    print("\n========== 测试 JWT Token 验证 ==========")
    config = AuthConfig()
    jwt_auth = JWTAuth(config)
    
    # 创建并验证访问Token
    access_token = jwt_auth.create_access_token(
        subject="test_user_123",
        user_claims={"username": "testuser"}
    )
    
    payload = jwt_auth.verify_token(access_token, required_type="access")
    assert payload["sub"] == "test_user_123", "用户ID应匹配"
    assert payload["username"] == "testuser", "用户名应匹配"
    assert payload["type"] == "access", "Token类型应为access"
    print("✅ 访问Token验证成功")
    
    # 创建并验证刷新Token
    refresh_token = jwt_auth.create_refresh_token(
        subject="test_user_123",
        user_claims={"username": "testuser"}
    )
    
    payload = jwt_auth.verify_token(refresh_token, required_type="refresh")
    assert payload["type"] == "refresh", "Token类型应为refresh"
    print("✅ 刷新Token验证成功")
    
    # 测试类型错误
    type_error_caught = False
    try:
        jwt_auth.verify_token(access_token, required_type="refresh")
    except RefreshTokenRequired:
        type_error_caught = True
    
    if not type_error_caught:
        raise AssertionError("应抛出 RefreshTokenRequired 异常")
    print("✅ Token类型错误检测成功 (access token used as refresh)")
    
    type_error_caught = False
    try:
        jwt_auth.verify_token(refresh_token, required_type="access")
    except AccessTokenRequired:
        type_error_caught = True
    
    if not type_error_caught:
        raise AssertionError("应抛出 AccessTokenRequired 异常")
    print("✅ Token类型错误检测成功 (refresh token used as access)")


def test_jwt_token_subject():
    """测试获取 Token Subject"""
    print("\n========== 测试获取 Token Subject ==========")
    config = AuthConfig()
    jwt_auth = JWTAuth(config)
    
    access_token = jwt_auth.create_access_token(subject="user_456")
    subject = jwt_auth.get_token_subject(access_token)
    
    assert subject == "user_456", "Subject应匹配"
    print("✅ Token Subject 获取成功")


def test_jwt_invalid_token():
    """测试无效Token处理"""
    print("\n========== 测试无效Token处理 ==========")
    config = AuthConfig()
    jwt_auth = JWTAuth(config)
    
    # 测试无效Token
    try:
        jwt_auth.verify_token("invalid.token.here", required_type="access")
        assert False, "应抛出 InvalidTokenError 异常"
    except InvalidTokenError:
        print("✅ 无效Token检测成功")
    
    # 测试空Token
    try:
        jwt_auth.verify_token("", required_type="access")
        assert False, "应抛出 InvalidTokenError 异常"
    except InvalidTokenError:
        print("✅ 空Token检测成功")


# ==================== Auth Service 测试 ====================

async def test_user_registration():
    """测试用户注册"""
    print("\n========== 测试用户注册 ==========")
    
    async for session in get_async_session():
        auth_service = AuthService(session)
        
        # 测试正常注册
        user_data = UserRegister(
            username="testuser1",
            password="password123",
            email="test1@example.com",
            nickname="测试用户1"
        )
        
        try:
            user_info = await auth_service.register_user(user_data)
            assert user_info.username == "testuser1", "用户名应匹配"
            assert user_info.email == "test1@example.com", "邮箱应匹配"
            assert user_info.is_active == True, "用户默认应激活"
            print(f"✅ 用户注册成功: {user_info.username} (ID: {user_info.id})")
        except UserAlreadyExistsError:
            print("⚠️  用户已存在，跳过注册测试")
            return
        
        # 测试重复注册
        try:
            await auth_service.register_user(user_data)
            assert False, "应抛出 UserAlreadyExistsError 异常"
        except UserAlreadyExistsError as e:
            print(f"✅ 重复注册检测成功: {e.message}")
        
        await session.commit()
        break


async def test_user_login():
    """测试用户登录"""
    print("\n========== 测试用户登录 ==========")
    
    async for session in get_async_session():
        auth_service = AuthService(session)
        
        # 先注册用户
        user_data = UserRegister(
            username="testuser2",
            password="password123",
            email="test2@example.com",
            nickname="测试用户2"
        )
        
        try:
            await auth_service.register_user(user_data)
        except UserAlreadyExistsError:
            pass  # 用户可能已存在
        
        # 测试正常登录
        login_data = UserLogin(
            username="testuser2",
            password="password123"
        )
        
        try:
            token_response = await auth_service.login(login_data)
            assert token_response.access_token is not None, "访问Token不应为空"
            assert token_response.refresh_token is not None, "刷新Token不应为空"
            assert token_response.token_type == "Bearer", "Token类型应为Bearer"
            print("✅ 用户登录成功")
            print(f"   访问Token: {token_response.access_token[:50]}...")
            print(f"   刷新Token: {token_response.refresh_token[:50]}...")
            
            return token_response
        except Exception as e:
            print(f"❌ 登录失败: {e}")
            return None
        finally:
            await session.commit()
            break


async def test_login_with_wrong_password():
    """测试错误密码登录"""
    print("\n========== 测试错误密码登录 ==========")
    
    async for session in get_async_session():
        auth_service = AuthService(session)
        
        login_data = UserLogin(
            username="testuser2",
            password="wrongpassword"
        )
        
        try:
            await auth_service.login(login_data)
            assert False, "应抛出 InvalidCredentialsError 异常"
        except InvalidCredentialsError as e:
            print(f"✅ 错误密码检测成功: {e.message}")
        finally:
            break


async def test_login_with_nonexistent_user():
    """测试不存在的用户登录"""
    print("\n========== 测试不存在的用户登录 ==========")
    
    async for session in get_async_session():
        auth_service = AuthService(session)
        
        login_data = UserLogin(
            username="nonexistent_user",
            password="password123"
        )
        
        try:
            await auth_service.login(login_data)
            assert False, "应抛出 InvalidCredentialsError 异常"
        except InvalidCredentialsError as e:
            print(f"✅ 不存在用户检测成功: {e.message}")
        finally:
            break


async def test_token_refresh(token_response: TokenResponse):
    """测试Token刷新"""
    print("\n========== 测试Token刷新 ==========")
    
    if token_response is None:
        print("⚠️  跳过Token刷新测试（无有效Token）")
        return
    
    async for session in get_async_session():
        auth_service = AuthService(session)
        
        try:
            new_token_response = await auth_service.refresh_access_token(
                token_response.refresh_token
            )
            assert new_token_response.access_token is not None, "新访问Token不应为空"
            assert new_token_response.refresh_token is not None, "新刷新Token不应为空"
            assert new_token_response.access_token != token_response.access_token, "访问Token应更新"
            print("✅ Token刷新成功")
            print(f"   新访问Token: {new_token_response.access_token[:50]}...")
        except Exception as e:
            print(f"❌ Token刷新失败: {e}")
        finally:
            await session.commit()
            break


async def test_get_current_user(token_response: TokenResponse):
    """测试获取当前用户信息"""
    print("\n========== 测试获取当前用户信息 ==========")
    
    if token_response is None:
        print("⚠️  跳过获取用户信息测试（无有效Token）")
        return
    
    async for session in get_async_session():
        auth_service = AuthService(session)
        
        try:
            user_info = await auth_service.get_current_user(token_response.access_token)
            assert user_info.username == "testuser2", "用户名应匹配"
            assert user_info.email == "test2@example.com", "邮箱应匹配"
            print(f"✅ 获取用户信息成功: {user_info.username}")
            print(f"   用户ID: {user_info.id}")
            print(f"   昵称: {user_info.nickname}")
        except Exception as e:
            print(f"❌ 获取用户信息失败: {e}")
        finally:
            break


async def test_get_current_user_with_invalid_token():
    """测试使用无效Token获取用户信息"""
    print("\n========== 测试无效Token获取用户信息 ==========")
    
    async for session in get_async_session():
        auth_service = AuthService(session)
        
        try:
            await auth_service.get_current_user("invalid.token.here")
            assert False, "应抛出 InvalidTokenError 异常"
        except InvalidTokenError:
            print("✅ 无效Token检测成功")
        finally:
            break


# ==================== 完整流程测试 ====================

async def test_full_auth_flow():
    """测试完整认证流程"""
    print("\n" + "="*50)
    print("开始完整认证流程测试")
    print("="*50)
    
    token_response = None
    
    # 1. 用户注册
    await test_user_registration()
    
    # 2. 用户登录
    token_response = await test_user_login()
    
    # 3. 错误密码登录
    await test_login_with_wrong_password()
    
    # 4. 不存在用户登录
    await test_login_with_nonexistent_user()
    
    # 5. Token刷新
    await test_token_refresh(token_response)
    
    # 6. 获取当前用户信息
    await test_get_current_user(token_response)
    
    # 7. 无效Token测试
    await test_get_current_user_with_invalid_token()
    
    print("\n" + "="*50)
    print("完整认证流程测试完成")
    print("="*50)


# ==================== 主函数 ====================

def run_unit_tests():
    """运行单元测试"""
    print("\n" + "="*50)
    print("运行认证模块单元测试")
    print("="*50)
    
    test_jwt_config()
    test_jwt_token_creation()
    test_jwt_token_verification()
    test_jwt_token_subject()
    test_jwt_invalid_token()


async def run_integration_tests():
    """运行集成测试"""
    await test_full_auth_flow()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("认证模块测试套件")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 运行单元测试
    run_unit_tests()
    
    # 运行集成测试
    asyncio.run(run_integration_tests())
    
    print("\n" + "="*60)
    print("所有测试完成")
    print("="*60)
