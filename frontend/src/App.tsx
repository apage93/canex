import { useState, useCallback } from 'react';
import { SessionInfo } from './types';
import LobbyPage from './components/LobbyPage';
import GamePage from './components/GamePage';

// sessionStorage is tab-scoped, so each browser tab gets its own player session.
// This allows multiple players to use different tabs on the same computer.
const SS_KEY = 'monopoly_session';

function loadSession(): SessionInfo | null {
  try {
    const raw = sessionStorage.getItem(SS_KEY);
    return raw ? (JSON.parse(raw) as SessionInfo) : null;
  } catch {
    return null;
  }
}

function saveSession(info: SessionInfo) {
  sessionStorage.setItem(SS_KEY, JSON.stringify(info));
}

function clearSession() {
  sessionStorage.removeItem(SS_KEY);
}

export default function App() {
  const urlParams = new URLSearchParams(window.location.search);
  const codeFromUrl = urlParams.get('code') ?? '';

  const [session, setSession] = useState<SessionInfo | null>(() => {
    // If the URL carries a join code, always start at the lobby so a second
    // player can join even when this tab inherited sessionStorage from another
    // tab (e.g. Ctrl+Click, "Duplicate Tab").
    if (codeFromUrl) return null;
    return loadSession();
  });

  const handleJoined = useCallback((info: SessionInfo) => {
    saveSession(info);
    setSession(info);
    // Clean the URL so refreshing doesn't re-trigger the code
    window.history.replaceState({}, '', '/');
  }, []);

  const handleLeave = useCallback(() => {
    clearSession();
    setSession(null);
  }, []);

  const handleInvalidSession = useCallback(() => {
    clearSession();
    setSession(null);
  }, []);

  if (session) {
    return (
      <GamePage
        session={session}
        onLeave={handleLeave}
        onInvalidSession={handleInvalidSession}
      />
    );
  }

  return <LobbyPage initialCode={codeFromUrl} onJoined={handleJoined} />;
}

