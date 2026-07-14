import { useState } from "react";
import { CreateGame } from "./CreateGame";
import { GameView } from "./GameView";

function App() {
  const [session, setSession] = useState<{ gameId: string; yourId: string } | null>(null);

  if (!session) {
    return (
      <CreateGame
        onCreated={(gameId, yourId) => setSession({ gameId, yourId })}
      />
    );
  }

  return <GameView gameId={session.gameId} yourId={session.yourId} />;
}

export default App;
