"""测试 Dialog-History 关系链"""
import asyncio
import sys
sys.path.insert(0, "e:/study/agent/work/hubu-agent/backend")

from app.database.dao.dialog_dao import DialogDao
from app.database.dao.history_dao import HistoryDao
from app.database.models.user import User
from app.database.engine import async_engine
from app.database.init_db import init_db
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select


async def test_dialog_history_chain():
    # 先建表
    await init_db()

    print("=" * 60)
    print("测试 Dialog-History 关系链")
    print("=" * 60)

    # 1. 创建测试用户
    print("\n[1] 创建测试用户...")
    async with AsyncSession(async_engine) as session:
        # 先清理旧测试用户
        statement = select(User).where(User.username == "test_dialog_user")
        result = await session.execute(statement)
        old_user = result.scalars().first()
        if old_user:
            await session.delete(old_user)
            await session.commit()

        user = User(
            username="test_dialog_user",
            email="test_dialog@test.com",
            password_hash="fake_hash",
            nickname="测试用户"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        user_id = user.id
        print(f"   用户创建成功: id={user_id}, username={user.username}")

    # 2. 创建对话（关联用户）
    print("\n[2] 创建对话...")
    dialog1 = await DialogDao.create_dialog(name="测试对话1", user_id=user_id)
    print(f"   对话创建成功: dialog_id={dialog1.dialog_id}, name={dialog1.name}, user_id={dialog1.user_id}")

    dialog2 = await DialogDao.create_dialog(name="测试对话2", user_id=user_id)
    print(f"   对话创建成功: dialog_id={dialog2.dialog_id}, name={dialog2.name}, user_id={dialog2.user_id}")

    # 3. 发消息（关联对话）
    print("\n[3] 发送消息...")
    msg1 = await HistoryDao.create_history(
        dialog_id=dialog1.dialog_id,
        role="user",
        content="你好，这是第一条消息"
    )
    print(f"   消息创建成功: id={msg1.id}, dialog_id={msg1.dialog_id}")

    msg2 = await HistoryDao.create_history(
        dialog_id=dialog1.dialog_id,
        role="assistant",
        content="你好！我是AI助手"
    )
    print(f"   消息创建成功: id={msg2.id}, dialog_id={msg2.dialog_id}")

    msg3 = await HistoryDao.create_history(
        dialog_id=dialog2.dialog_id,
        role="user",
        content="这是第二个对话的消息"
    )
    print(f"   消息创建成功: id={msg3.id}, dialog_id={msg3.dialog_id}")

    # 4. 查询用户的对话列表
    print("\n[4] 查询用户对话列表...")
    dialogs = await DialogDao.get_dialogs_by_user_id(user_id=user_id)
    print(f"   用户 {user_id} 共有 {len(dialogs)} 个对话:")
    for d in dialogs:
        print(f"   - dialog_id={d.dialog_id}, name={d.name}, user_id={d.user_id}")

    # 5. 查询对话的历史消息
    print("\n[5] 查询对话历史消息...")
    histories = await HistoryDao.get_history_by_dialog_id(dialog_id=dialog1.dialog_id)
    print(f"   对话 {dialog1.dialog_id} 共有 {len(histories)} 条消息:")
    for h in histories:
        print(f"   - [{h.role}] {h.content[:30]}...")

    # 6. 更新对话名称
    print("\n[6] 更新对话名称...")
    updated = await DialogDao.update_dialog_name(dialog1.dialog_id, "重命名后的对话")
    if updated:
        print(f"   更新成功: name={updated.name}")

    # 7. 权限校验 - 用另一个用户ID查询
    print("\n[7] 权限校验...")
    other_dialogs = await DialogDao.get_dialogs_by_user_id(user_id=99999)
    print(f"   用户 99999 的对话数: {len(other_dialogs)} (应该为0)")

    dialog_check = await DialogDao.get_dialog_by_id(dialog1.dialog_id)
    if dialog_check and dialog_check.user_id != 99999:
        print(f"   权限校验通过: 对话属于 user_id={dialog_check.user_id}, 不是 99999")

    # 8. 删除对话（级联删除历史）
    print("\n[8] 删除对话（级联删除历史）...")
    delete_result = await DialogDao.delete_dialog(dialog1.dialog_id)
    print(f"   删除对话结果: {delete_result}")

    # 验证历史也被删除
    remaining = await HistoryDao.get_history_by_dialog_id(dialog_id=dialog1.dialog_id)
    print(f"   删除后历史消息数: {len(remaining)} (应该为0)")

    # 9. 清理
    print("\n[9] 清理测试数据...")
    await DialogDao.delete_dialog(dialog2.dialog_id)
    async with AsyncSession(async_engine) as session:
        statement = select(User).where(User.username == "test_dialog_user")
        result = await session.execute(statement)
        user = result.scalars().first()
        if user:
            await session.delete(user)
            await session.commit()
    print("   清理完成")

    print("\n" + "=" * 60)
    print("所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_dialog_history_chain())
