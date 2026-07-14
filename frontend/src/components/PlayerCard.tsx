import { Player } from '../types';

export const PLAYER_COLORS = ['#3b82f6', '#ef4444', '#22c55e', '#f59e0b'];
export const PLAYER_EMOJIS = ['🎩', '🚂', '🐶', '⚓'];

interface Props {
  player: Player;
  playerIndex: number;
  isCurrentTurn: boolean;
  isMe: boolean;
  board: { id: number; name: string }[];
}

export default function PlayerCard({ player, playerIndex, isCurrentTurn, isMe, board }: Props) {
  const color = PLAYER_COLORS[playerIndex];
  const emoji = PLAYER_EMOJIS[playerIndex];

  return (
    <div style={{
      background: 'var(--surface2)',
      borderRadius: '12px',
      padding: '0.9rem 1rem',
      border: `2px solid ${isCurrentTurn ? color : 'transparent'}`,
      opacity: player.is_bankrupt ? 0.45 : 1,
      transition: 'border-color 0.3s',
      position: 'relative',
    }}>
      {isCurrentTurn && !player.is_bankrupt && (
        <div style={{
          position: 'absolute',
          top: '0.5rem',
          right: '0.6rem',
          fontSize: '10px',
          color,
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '1px',
        }}>
          ▶ Turn
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem' }}>
        <span style={{ fontSize: '1.4rem' }}>{emoji}</span>
        <div>
          <div style={{
            fontWeight: 700,
            color: player.is_bankrupt ? 'var(--text-muted)' : color,
            textDecoration: player.is_bankrupt ? 'line-through' : 'none',
            fontSize: '0.95rem',
          }}>
            {player.name}
            {isMe && <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: '0.75rem', marginLeft: '0.4rem' }}>(you)</span>}
            {player.is_host && <span style={{ color: 'var(--text-muted)', fontWeight: 400, fontSize: '0.75rem', marginLeft: '0.4rem' }}>👑</span>}
          </div>
          {player.is_bankrupt
            ? <div style={{ fontSize: '0.78rem', color: 'var(--danger)' }}>
                {player.has_quit ? '🚪 Logout' : '💸 Bankrupt'}
              </div>
            : <div style={{ fontSize: '0.85rem', color: 'var(--accent)' }}>${player.money.toLocaleString()}</div>
          }
        </div>
      </div>

      {player.properties.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
          {player.properties.map((id) => {
            const square = board.find(s => s.id === id);
            return (
              <span key={id} style={{
                fontSize: '10px',
                padding: '2px 6px',
                background: 'var(--surface)',
                borderRadius: '4px',
                color: 'var(--text-muted)',
                whiteSpace: 'nowrap',
              }}>
                {square?.name ?? `#${id}`}
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}

