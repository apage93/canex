import React from 'react';
import { Square, Player } from '../types';
import { PLAYER_COLORS, PLAYER_EMOJIS } from './PlayerCard';

// ── Board layout ──────────────────────────────────────────────────────────────
// 7×7 CSS grid; squares occupy the border cells, center is game info.
//
//  col:  0    1    2    3    4    5    6
// row 0: [12] [13] [14] [15] [16] [17] [18]
// row 1: [11]  ·    ·    ·    ·    ·  [19]
// row 2: [10]  ·    ·    ·    ·    ·  [20]
// row 3: [ 9]  ·    ·    ·    ·    ·  [21]
// row 4: [ 8]  ·    ·    ·    ·    ·  [22]
// row 5: [ 7]  ·    ·    ·    ·    ·  [23]
// row 6: [ 6] [ 5] [ 4] [ 3] [ 2] [ 1] [ 0←GO]

const GRID_POS: Array<{ row: number; col: number }> = [
  { row: 6, col: 6 }, // 0  GO
  { row: 6, col: 5 }, // 1
  { row: 6, col: 4 }, // 2
  { row: 6, col: 3 }, // 3
  { row: 6, col: 2 }, // 4
  { row: 6, col: 1 }, // 5
  { row: 6, col: 0 }, // 6
  { row: 5, col: 0 }, // 7
  { row: 4, col: 0 }, // 8
  { row: 3, col: 0 }, // 9
  { row: 2, col: 0 }, // 10
  { row: 1, col: 0 }, // 11
  { row: 0, col: 0 }, // 12
  { row: 0, col: 1 }, // 13
  { row: 0, col: 2 }, // 14
  { row: 0, col: 3 }, // 15
  { row: 0, col: 4 }, // 16
  { row: 0, col: 5 }, // 17
  { row: 0, col: 6 }, // 18
  { row: 1, col: 6 }, // 19
  { row: 2, col: 6 }, // 20
  { row: 3, col: 6 }, // 21
  { row: 4, col: 6 }, // 22
  { row: 5, col: 6 }, // 23
];

const CORNERS = new Set([0, 6, 12, 18]);

const PROPERTY_COLORS: Record<string, string> = {
  purple:    '#a855f7',
  lightblue: '#38bdf8',
  pink:      '#f472b6',
  red:       '#ef4444',
  railroad:  '#475569',
  green:     '#22c55e',
};

const CELL = 68; // px

type Side = 'top' | 'bottom' | 'left' | 'right';

function getSide(row: number, col: number): Side {
  if (row === 0) return 'top';
  if (row === 6) return 'bottom';
  if (col === 0) return 'left';
  return 'right';
}

function colorStripStyle(side: Side, hex: string): React.CSSProperties {
  const base: React.CSSProperties = { position: 'absolute', backgroundColor: hex };
  switch (side) {
    case 'bottom': return { ...base, top: 0,    left: 0,    right: 0,    height: 12 };
    case 'top':    return { ...base, bottom: 0,  left: 0,    right: 0,    height: 12 };
    case 'left':   return { ...base, top: 0,    bottom: 0,  right: 0,    width:  12 };
    case 'right':  return { ...base, top: 0,    bottom: 0,  left: 0,     width:  12 };
  }
}

function contentPadding(side: Side, hasStrip: boolean): React.CSSProperties {
  if (!hasStrip) return {};
  switch (side) {
    case 'bottom': return { paddingTop:    13 };
    case 'top':    return { paddingBottom: 13 };
    case 'left':   return { paddingRight:  13 };
    case 'right':  return { paddingLeft:   13 };
  }
}

// ── Square cell ───────────────────────────────────────────────────────────────
interface CellProps {
  square: Square;
  pos: { row: number; col: number };
  playersHere: Player[];
  ownerIndex: number | undefined;
  playerIndexMap: Map<string, number>;
}

function SquareCell({ square, pos, playersHere, ownerIndex, playerIndexMap }: CellProps) {
  const { row, col } = pos;
  const isCorner = CORNERS.has(square.id);
  const side = getSide(row, col);
  const hexColor = square.color ? PROPERTY_COLORS[square.color] : undefined;
  const ownerColor = ownerIndex !== undefined ? PLAYER_COLORS[ownerIndex] : undefined;

  return (
    <div
      style={{
        gridRow: row + 1,
        gridColumn: col + 1,
        width: CELL,
        height: CELL,
        border: '1px solid #2d6a1f',
        background: ownerColor ? `${ownerColor}18` : '#f8f4e3',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: 7,
        fontWeight: 500,
        color: '#1a1a1a',
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Coloured property strip */}
      {hexColor && !isCorner && <div style={colorStripStyle(side, hexColor)} />}

      {/* Content wrapper */}
      <div style={{
        zIndex: 1,
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 2,
        ...contentPadding(side, Boolean(hexColor && !isCorner)),
      }}>
        {/* Corner icons */}
        {square.id === 0  && <span style={{ fontSize: 20 }}>🚦</span>}
        {square.id === 6  && <span style={{ fontSize: 18 }}>🏛️</span>}
        {square.id === 12 && <span style={{ fontSize: 20 }}>🅿️</span>}
        {square.id === 18 && <span style={{ fontSize: 18 }}>🚔</span>}

        <div style={{ fontWeight: 700, lineHeight: 1.2, wordBreak: 'break-word' }}>
          {square.name}
        </div>
        {square.price != null && (
          <div style={{ color: '#374151', marginTop: 1 }}>${square.price}</div>
        )}

        {/* Player tokens */}
        {playersHere.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center', marginTop: 2 }}>
            {playersHere.map((p) => {
              const idx = playerIndexMap.get(p.id) ?? 0;
              return (
                <div
                  key={p.id}
                  title={p.name}
                  style={{
                    width: 11,
                    height: 11,
                    borderRadius: '50%',
                    background: PLAYER_COLORS[idx],
                    border: '1.5px solid white',
                    fontSize: 7,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontWeight: 700,
                  }}
                >
                  {PLAYER_EMOJIS[idx]}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Owner dot */}
      {ownerColor && (
        <div style={{
          position: 'absolute',
          top: 2,
          right: 2,
          width: 6,
          height: 6,
          borderRadius: '50%',
          background: ownerColor,
          zIndex: 2,
        }} />
      )}
    </div>
  );
}

// ── Board ─────────────────────────────────────────────────────────────────────
interface BoardProps {
  board: Square[];
  players: Player[];
  propertyOwners: Record<string, string>;
  lastAction: string;
}

export default function Board({ board, players, propertyOwners, lastAction }: BoardProps) {
  // Map player id → array index (for colour assignment)
  const playerIndexMap = new Map<string, number>(players.map((p, i) => [p.id, i]));

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(7, ${CELL}px)`,
        gridTemplateRows:    `repeat(7, ${CELL}px)`,
        border: '3px solid #166534',
        borderRadius: 4,
        boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
        flexShrink: 0,
      }}
    >
      {/* Board squares */}
      {board.map((square) => {
        const pos = GRID_POS[square.id];
        const playersHere = players.filter((p) => p.position === square.id && !p.is_bankrupt);
        const ownerId = propertyOwners[String(square.id)];
        const ownerIndex = ownerId !== undefined ? playerIndexMap.get(ownerId) : undefined;

        return (
          <SquareCell
            key={square.id}
            square={square}
            pos={pos}
            playersHere={playersHere}
            ownerIndex={ownerIndex}
            playerIndexMap={playerIndexMap}
          />
        );
      })}

      {/* Centre panel */}
      <div
        style={{
          gridRow: '2 / 7',
          gridColumn: '2 / 7',
          background: 'linear-gradient(135deg, #14532d 0%, #166534 50%, #15803d 100%)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#dcfce7',
          padding: '1rem',
          textAlign: 'center',
          gap: '0.5rem',
        }}
      >
        <div style={{ fontSize: '1.5rem', fontWeight: 900, letterSpacing: '6px', color: '#bbf7d0' }}>
          MONOPOLY
        </div>
        <div style={{ width: 60, height: 2, background: '#86efac', borderRadius: 2 }} />
        <div style={{
          fontSize: '11px',
          color: '#86efac',
          maxWidth: 260,
          lineHeight: 1.5,
          marginTop: '0.25rem',
          background: 'rgba(0,0,0,0.2)',
          borderRadius: 8,
          padding: '0.5rem 0.75rem',
        }}>
          {lastAction}
        </div>
      </div>
    </div>
  );
}

