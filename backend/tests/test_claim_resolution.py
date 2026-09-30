# test_claim_resolution.py
import asyncio, os, sys
from unittest.mock import AsyncMock, MagicMock, patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('BOT_TOKEN', 'test-token')
os.environ.setdefault('DATABASE_URL', 'postgresql://fake/fake')
import bot
from bot import resolve_game_sync, queue_broadcast, drain_broadcasts, PENDING_BROADCASTS

def test_resolve_game_sync_returns_false_when_already_finished():
    with patch.object(bot.db, 'get_game', return_value={'state': 'finished', 'pool': 100, 'room_fee': 5}):
        assert resolve_game_sync(1, 5, {123: {0: 'line'}}) is False

def test_resolve_game_sync_credits_winners_and_finishes_game():
    fake_game = {'state': 'running', 'pool': 1000, 'room_fee': 5}
    with patch.object(bot.db, 'get_game', return_value=fake_game), \
         patch.object(bot.db, 'credit_house') as mc, \
         patch.object(bot.db, 'adjust_balance') as ma, \
         patch.object(bot.db, 'record_transaction') as mt, \
         patch.object(bot.db, 'finish_game') as mf, \
         patch.object(bot.db, 'get_user', return_value={'username': 'alice'}), \
         patch.object(bot.db, 'get_player_cards', return_value=[0]), \
         patch('bot.queue_broadcast') as mq:
        assert resolve_game_sync(1, 5, {123: {0: 'line'}}) is True
        mc.assert_called_once(); ma.assert_called_once(); mt.assert_called_once()
        mf.assert_called_once(); mq.assert_called_once()

def test_resolve_game_sync_queues_broadcast():
    fake_game = {'state': 'running', 'pool': 1000, 'room_fee': 5}
    with patch.object(bot.db, 'get_game', return_value=fake_game), \
         patch.object(bot.db, 'credit_house'), patch.object(bot.db, 'adjust_balance'), \
         patch.object(bot.db, 'record_transaction'), patch.object(bot.db, 'finish_game'), \
         patch.object(bot.db, 'get_user', return_value={'username': 'alice'}), \
         patch.object(bot.db, 'get_player_cards', return_value=[0]):
        resolve_game_sync(1, 5, {123: {0: 'line'}})
        assert 1 in PENDING_BROADCASTS
        assert 'Winners' in PENDING_BROADCASTS[1]

def test_drain_broadcasts_sends_queued_announcement():
    queue_broadcast(1, 'test announcement')
    fake_bot = MagicMock()
    with patch('bot.group_broadcast', new=AsyncMock()) as mb:
        asyncio.run(drain_broadcasts(fake_bot, 1))
        mb.assert_awaited_once_with(fake_bot, 1, 'test announcement')
        assert 1 not in PENDING_BROADCASTS

def test_drain_broadcasts_noop_when_nothing_queued():
    fake_bot = MagicMock()
    with patch('bot.group_broadcast', new=AsyncMock()) as mb:
        asyncio.run(drain_broadcasts(fake_bot, 999))
        mb.assert_not_awaited()

def test_queue_broadcast_is_thread_safe():
    import threading
    def writer():
        for i in range(100):
            queue_broadcast(i, 'msg-' + str(i))
    threads = [threading.Thread(target=writer) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(PENDING_BROADCASTS) == 100
    for i in range(100):
        assert PENDING_BROADCASTS[i] == 'msg-' + str(i)
