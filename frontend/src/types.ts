export interface Square {
  id: number;
  type: 'go' | 'property' | 'empty';
  name: string;
  price: number | null;
  rent: number | null;
  color: string | null;
}

export interface Player {
  id: string;
  name: string;
  money: number;
  position: number;
  properties: number[];
  is_bankrupt: boolean;
  is_host: boolean;
}

export interface GameState {
  game_id: string;
  join_code: string;
  status: 'waiting' | 'playing' | 'finished';
  players: Player[];
  current_player_index: number;
  property_owners: Record<string, string>; // squareId -> playerId
  board: Square[];
  last_action: string;
  winner: string | null;
}

export interface SessionInfo {
  game_id: string;
  player_id: string;
  player_name: string;
}

