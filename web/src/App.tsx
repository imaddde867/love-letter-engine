import { useState } from "react";
import { CreateGame } from "./CreateGame";
import { GameView } from "./GameView";

function App() {
  const [session, setSession] = useState<{
    gameId: string;
    yourId: string;
    token: string;
  } | null>(null);

  if (!session) {
    return (
      <CreateGame
        onCreated={(gameId, yourId, token) => setSession({ gameId, yourId, token })}
      />
    );
  }

  return <GameView gameId={session.gameId} yourId={session.yourId} token={session.token} />;
}

export default App;
