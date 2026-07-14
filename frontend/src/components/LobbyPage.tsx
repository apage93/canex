import { useEffect, useState } from 'react';
import { SessionInfo } from '../types';

interface Props {
  initialCode: string;
  onJoined: (info: SessionInfo) => void;
}

type Tab = 'create' | 'join';

export default function LobbyPage({ initialCode, onJoined }: Props) {
  const [tab, setTab] = useState<Tab>(initialCode ? 'join' : 'create');
  const [hasWaitingGames, setHasWaitingGames] = useState(!!initialCode);

  useEffect(() => {
    fetch('/api/games')
      .then((r) => r.json())
      .then((games: unknown[]) => setHasWaitingGames(games.length > 0))
      .catch(() => setHasWaitingGames(false));
  }, []);

  // Create game form
  const [createName, setCreateName] = useState('');
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState('');

  // Join game form
  const [joinCode, setJoinCode] = useState(initialCode);
  const [joinName, setJoinName] = useState('');
  const [joinLoading, setJoinLoading] = useState(false);
  const [joinError, setJoinError] = useState('');

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createName.trim()) return;
    setCreateLoading(true);
    setCreateError('');
    try {
      const res = await fetch('/api/games', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_name: createName.trim() }),
      });
      if (!res.ok) throw new Error((await res.json()).detail ?? 'Error');
      const data = await res.json() as SessionInfo;
      onJoined(data);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create game');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleJoin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!joinCode.trim() || !joinName.trim()) return;
    setJoinLoading(true);
    setJoinError('');
    try {
      const res = await fetch(`/api/games/join?code=${encodeURIComponent(joinCode.trim())}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_name: joinName.trim() }),
      });
      if (!res.ok) throw new Error((await res.json()).detail ?? 'Error');
      const data = await res.json() as SessionInfo;
      onJoined(data);
    } catch (err) {
      setJoinError(err instanceof Error ? err.message : 'Failed to join game');
    } finally {
      setJoinLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg)',
      padding: '2rem',
    }}>
      <div style={{
        background: 'var(--surface)',
        borderRadius: '16px',
        padding: '2.5rem',
        width: '100%',
        maxWidth: '420px',
        boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ fontSize: '3rem' }}>🎲</div>
          <h1 style={{
            fontSize: '2rem',
            fontWeight: 800,
            letterSpacing: '6px',
            color: 'var(--accent)',
            textTransform: 'uppercase',
          }}>
            Monopoly
          </h1>
          <p style={{ color: 'var(--text-muted)', marginTop: '0.25rem', fontSize: '0.85rem' }}>
            Multiplayer Web Edition
          </p>
        </div>

        {/* Tabs */}
        <div style={{
          display: 'flex',
          background: 'var(--surface2)',
          borderRadius: '10px',
          padding: '4px',
          marginBottom: '1.5rem',
        }}>
          {(['create', 'join'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              disabled={t === 'join' && !hasWaitingGames}
              style={{
                flex: 1,
                background: tab === t ? 'var(--accent)' : 'transparent',
                color: tab === t ? '#fff' : 'var(--text-muted)',
                borderRadius: '8px',
                padding: '0.5rem',
                fontSize: '0.9rem',
              }}
            >
              {t === 'create' ? '🆕 Create Game' : '🔗 Join Game'}
            </button>
          ))}
        </div>

        {/* Create Game */}
        {tab === 'create' && (
          <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.4rem', display: 'block' }}>
                Your name
              </label>
              <input
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
                placeholder="e.g. Alice"
                maxLength={20}
                autoFocus
              />
            </div>
            {createError && (
              <div style={{ color: 'var(--danger)', fontSize: '0.85rem' }}>{createError}</div>
            )}
            <button
              type="submit"
              disabled={!createName.trim() || createLoading}
              style={{ background: 'var(--accent)', color: '#fff', padding: '0.75rem' }}
            >
              {createLoading ? 'Creating…' : 'Create Game'}
            </button>
          </form>
        )}

        {/* Join Game */}
        {tab === 'join' && (
          <form onSubmit={handleJoin} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.4rem', display: 'block' }}>
                Game code
              </label>
              <input
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
                placeholder="e.g. AB12CD"
                maxLength={6}
                style={{ fontFamily: 'monospace', fontSize: '1.2rem', letterSpacing: '4px', textAlign: 'center' }}
              />
            </div>
            <div>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.4rem', display: 'block' }}>
                Your name
              </label>
              <input
                value={joinName}
                onChange={(e) => setJoinName(e.target.value)}
                placeholder="e.g. Bob"
                maxLength={20}
              />
            </div>
            {joinError && (
              <div style={{ color: 'var(--danger)', fontSize: '0.85rem' }}>{joinError}</div>
            )}
            <button
              type="submit"
              disabled={joinCode.trim().length < 6 || !joinName.trim() || joinLoading}
              style={{ background: 'var(--accent)', color: '#fff', padding: '0.75rem' }}
            >
              {joinLoading ? 'Joining…' : 'Join Game'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

