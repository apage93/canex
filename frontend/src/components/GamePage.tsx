import { useEffect, useState, useCallback } from 'react';
import { SessionInfo } from '../types';
import { useGameWebSocket } from '../hooks/useGameWebSocket';
import Board from './Board';
import PlayerCard, { PLAYER_COLORS, PLAYER_EMOJIS } from './PlayerCard';

interface Props {
  session: SessionInfo;
  onLeave: () => void;
  onInvalidSession: () => void;
}

export default function GamePage({ session, onLeave, onInvalidSession }: Props) {
  const { gameState, wsError, connected, send, clearError } = useGameWebSocket(
    session.game_id,
    session.player_id,
    onInvalidSession,
  );

  const handleLeave = useCallback(() => {
    if (gameState?.status === 'playing') {
      send({ type: 'leave_game' });
    }
    onLeave();
  }, [gameState?.status, send, onLeave]);

  const [actionLog, setActionLog] = useState<string[]>([]);
  const [setCopied] = useState(false);

  useEffect(() => {
    if (gameState?.last_action) {
      setActionLog((prev) => {
        const last = prev[prev.length - 1];
        if (last === gameState.last_action) return prev; // no duplicate
        return [...prev.slice(-14), gameState.last_action];
      });
    }
  }, [gameState?.last_action]);

  const handleRoll = useCallback(() => {
    send({ type: 'roll_dice' });
  }, [send]);

  const handleStart = useCallback(() => {
    send({ type: 'start_game' });
  }, [send]);

  const copyLink = useCallback(() => {
    const url = `${window.location.origin}/?code=${gameState?.join_code ?? ''}`;
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [gameState?.join_code]);

  // ── Loading ──────────────────────────────────────────────────────────────────
  if (!gameState) {
    return (
      <div style={centeredStyle}>
        <div style={{ fontSize: '2rem' }}>⏳</div>
        <div style={{ color: 'var(--text-muted)', marginTop: '0.5rem' }}>
          {connected ? 'Loading game…' : 'Connecting…'}
        </div>
      </div>
    );
  }

  const { status, players, current_player_index, property_owners, board, join_code, winner } = gameState;

  const me = players.find((p) => p.id === session.player_id);
  const currentPlayer = players[current_player_index];
  const isMyTurn = me?.id === currentPlayer?.id && status === 'playing' && !me?.is_bankrupt;
  const isHost = me?.is_host ?? false;
  const activePlayers = players.filter((p) => !p.is_bankrupt);

  // ── Finished screen ──────────────────────────────────────────────────────────
  if (status === 'finished') {
    const winnerPlayer = players.find((p) => p.name === winner);
    const winnerIdx = winnerPlayer ? players.indexOf(winnerPlayer) : 0;

    return (
      <div style={centeredStyle}>
        <div style={{ fontSize: '4rem' }}>🏆</div>
        <h2 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent)', margin: '0.5rem 0' }}>
          {winner} wins!
        </h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
          {PLAYER_EMOJIS[winnerIdx]} Congratulations!
        </p>

        <div style={{ background: 'var(--surface)', borderRadius: 12, padding: '1rem', width: 300, marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Final standings</div>
          {[...players].sort((a, b) => b.money - a.money).map((p, _i) => {
            const idx = players.indexOf(p);
            return (
              <div key={p.id} style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '0.3rem 0',
                color: p.is_bankrupt ? 'var(--text-muted)' : 'var(--text)',
              }}>
                <span>{PLAYER_EMOJIS[idx]} {p.name}{p.id === session.player_id ? ' (you)' : ''}</span>
                <span style={{ color: p.is_bankrupt ? 'var(--danger)' : 'var(--accent)', fontWeight: 600 }}>
                  {p.is_bankrupt ? (p.has_quit ? '🚪 Logout' : '💸 Bankrupt') : `$${p.money.toLocaleString()}`}
                </span>
              </div>
            );
          })}
        </div>

        <button onClick={handleLeave} style={{ background: 'var(--accent)', color: '#fff', padding: '0.75rem 2rem' }}>
          Back to Lobby
        </button>
      </div>
    );
  }

  // ── Waiting room ─────────────────────────────────────────────────────────────
  if (status === 'waiting') {
    return (
      <div style={centeredStyle}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent)', marginBottom: '0.25rem' }}>
          🎲 Game Lobby
        </h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem', fontSize: '0.85rem' }}>
          {connected ? '🟢 Connected' : '🔴 Reconnecting…'}
        </p>

        {/* Join code */}
        <div style={{
          background: 'var(--surface)',
          borderRadius: 12,
          padding: '1rem 1.5rem',
          marginBottom: '1rem',
          textAlign: 'center',
          width: 320,
        }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Game Code</div>
          <div style={{ fontSize: '2rem', fontWeight: 900, letterSpacing: 8, fontFamily: 'monospace', color: 'var(--accent)' }}>
            {join_code}
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', justifyContent: 'center' }}>
            <button
              onClick={() => {
                const url = `${window.location.origin}/?code=${gameState?.join_code ?? ''}`;
                window.open(url, '_blank', 'noopener');
              }}
              style={{ background: 'var(--surface2)', color: 'var(--text)', fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
              title="Ouvre un nouvel onglet avec le formulaire de join pré-rempli"
            >
              ↗ Add player
            </button>
          </div>
        </div>

        {/* Players */}
        <div style={{ width: 320, marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
            Players ({players.length}/4)
          </div>
          {players.map((p, i) => (
            <div key={p.id} style={{
              display: 'flex', alignItems: 'center', gap: '0.5rem',
              padding: '0.5rem 0.75rem',
              background: 'var(--surface)',
              borderRadius: 8,
              marginBottom: 6,
              border: `1.5px solid ${PLAYER_COLORS[i]}40`,
            }}>
              <span style={{ fontSize: '1.2rem' }}>{PLAYER_EMOJIS[i]}</span>
              <span style={{ color: PLAYER_COLORS[i], fontWeight: 600 }}>{p.name}</span>
              {p.is_host && <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-muted)' }}>👑 Host</span>}
              {p.id === session.player_id && !p.is_host && <span style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--text-muted)' }}>You</span>}
            </div>
          ))}
          {players.length < 4 && (
            <div style={{
              padding: '0.5rem 0.75rem',
              background: 'var(--surface)',
              borderRadius: 8,
              color: 'var(--text-muted)',
              fontSize: '0.85rem',
              border: '1.5px dashed var(--border)',
            }}>
              Waiting for players…
            </div>
          )}
        </div>

        {isHost && (
          <button
            onClick={handleStart}
            disabled={players.length < 2}
            style={{ background: 'var(--accent)', color: '#fff', padding: '0.75rem 2rem', fontSize: '1rem' }}
          >
            🚀 Start Game
          </button>
        )}
        {!isHost && (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Waiting for host to start…</p>
        )}

        <button
          onClick={handleLeave}
          style={{ background: 'transparent', color: 'var(--text-muted)', marginTop: '1rem', fontSize: '0.8rem' }}
        >
          Leave
        </button>

        {wsError && <div style={{ color: 'var(--danger)', marginTop: '1rem', fontSize: '0.85rem' }}>{wsError}</div>}
      </div>
    );
  }

  // ── Playing ───────────────────────────────────────────────────────────────────
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      minHeight: '100vh',
      background: 'var(--bg)',
    }}>
      {/* Header */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.6rem 1.5rem',
        background: 'var(--surface)',
        borderBottom: '1px solid var(--border)',
        flexShrink: 0,
      }}>
        <div style={{ fontWeight: 800, fontSize: '1.1rem', letterSpacing: '3px', color: 'var(--accent)' }}>
          🎲 MONOPOLY
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{
            fontFamily: 'monospace', fontSize: '0.85rem', letterSpacing: 3,
            color: 'var(--text-muted)', background: 'var(--surface2)',
            borderRadius: 6, padding: '0.2rem 0.6rem',
          }}>
            {join_code}
          </span>
          <span style={{ fontSize: '0.75rem', color: connected ? 'var(--accent)' : 'var(--danger)' }}>
            {connected ? '🟢' : '🔴'}
          </span>
          <button
            onClick={handleLeave}
            style={{ background: 'transparent', color: 'var(--text-muted)', padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}
          >
            Leave
          </button>
        </div>
      </header>

      {/* Main */}
      <div style={{
        display: 'flex',
        flex: 1,
        gap: '1rem',
        padding: '1rem',
        alignItems: 'flex-start',
        justifyContent: 'center',
        flexWrap: 'wrap',
      }}>
        {/* Board */}
        <Board
          board={board}
          players={players}
          propertyOwners={property_owners}
          lastAction={gameState.last_action}
        />

        {/* Sidebar */}
        <div style={{
          width: 280,
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
          flexShrink: 0,
        }}>
          {/* Players */}
          <div style={{ background: 'var(--surface)', borderRadius: 12, padding: '0.75rem' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: 1 }}>
              Players
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {players.map((p, i) => (
                <PlayerCard
                  key={p.id}
                  player={p}
                  playerIndex={i}
                  isCurrentTurn={i === current_player_index && status === 'playing'}
                  isMe={p.id === session.player_id}
                  board={board}
                />
              ))}
            </div>
          </div>

          {/* Action panel */}
          <div style={{ background: 'var(--surface)', borderRadius: 12, padding: '0.75rem' }}>
            {isMyTurn ? (
              <>
                <div style={{ fontSize: '0.8rem', color: 'var(--accent)', marginBottom: '0.5rem', fontWeight: 600 }}>
                  ✨ Your turn!
                </div>
                <button
                  onClick={handleRoll}
                  style={{
                    width: '100%',
                    background: 'var(--accent)',
                    color: '#fff',
                    padding: '0.75rem',
                    fontSize: '1rem',
                    borderRadius: 10,
                  }}
                >
                  🎲 Roll Dice
                </button>
              </>
            ) : (
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textAlign: 'center', padding: '0.5rem 0' }}>
                {currentPlayer && !currentPlayer.is_bankrupt
                  ? `Waiting for ${currentPlayer.name} to roll…`
                  : 'Processing…'}
              </div>
            )}

            {wsError && (
              <div style={{
                marginTop: '0.5rem',
                background: '#450a0a',
                borderRadius: 6,
                padding: '0.4rem 0.6rem',
                fontSize: '0.8rem',
                color: '#fca5a5',
                cursor: 'pointer',
              }} onClick={clearError}>
                ⚠ {wsError}
              </div>
            )}
          </div>

          {/* Action log */}
          <div style={{ background: 'var(--surface)', borderRadius: 12, padding: '0.75rem', flex: 1, minHeight: 120 }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: 1 }}>
              Log
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', maxHeight: 250, overflowY: 'auto' }}>
              {actionLog.slice().reverse().map((entry, i) => (
                <div key={i} style={{
                  fontSize: '0.78rem',
                  color: i === 0 ? 'var(--text)' : 'var(--text-muted)',
                  lineHeight: 1.4,
                  padding: '0.2rem 0',
                  borderBottom: i < actionLog.length - 1 ? '1px solid var(--border)' : 'none',
                }}>
                  {entry}
                </div>
              ))}
            </div>
          </div>

          {/* Active count */}
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', textAlign: 'center' }}>
            {activePlayers.length} player{activePlayers.length !== 1 ? 's' : ''} remaining
          </div>
        </div>
      </div>
    </div>
  );
}

const centeredStyle: React.CSSProperties = {
  minHeight: '100vh',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  background: 'var(--bg)',
  padding: '2rem',
};

