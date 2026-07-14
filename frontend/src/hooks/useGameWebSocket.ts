import { useEffect, useRef, useState, useCallback } from 'react';
import { GameState } from '../types';

export function useGameWebSocket(
  gameId: string,
  playerId: string,
  onInvalidSession: () => void,
) {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [wsError, setWsError] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const shouldReconnect = useRef(true);

  const connect = useCallback(() => {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${proto}//${window.location.host}/api/games/${gameId}/ws?player_id=${playerId}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      setWsError(null);
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data as string) as { type: string; state?: GameState; message?: string };
      if (msg.type === 'game_state' && msg.state) {
        setGameState(msg.state);
      } else if (msg.type === 'error') {
        setWsError(msg.message ?? 'Unknown error');
      }
    };

    ws.onerror = () => {
      setWsError('WebSocket connection error');
    };

    ws.onclose = (event) => {
      setConnected(false);
      if (event.code === 1008) {
        // Server rejected: invalid game or player
        onInvalidSession();
      } else if (shouldReconnect.current) {
        setTimeout(connect, 2000);
      }
    };
  }, [gameId, playerId, onInvalidSession]);

  useEffect(() => {
    shouldReconnect.current = true;
    connect();
    return () => {
      shouldReconnect.current = false;
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((msg: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  const clearError = useCallback(() => setWsError(null), []);

  return { gameState, wsError, connected, send, clearError };
}

