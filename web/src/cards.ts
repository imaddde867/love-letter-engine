export const CARD_NAMES: Record<number, string> = {
  0: "spy",
  1: "guard",
  2: "priest",
  3: "baron",
  4: "handmaid",
  5: "prince",
  6: "chancellor",
  7: "king",
  8: "countess",
  9: "princess",
};

export function cardImage(value: number): string {
  return `/cards/${CARD_NAMES[value]}.png`;
}

export const CARD_BACK = "/cards/cardback.png";

export function cardLabel(value: number): string {
  const name = CARD_NAMES[value];
  return name ? name[0].toUpperCase() + name.slice(1) : `Card ${value}`;
}

export const CARD_EFFECTS: Record<number, string> = {
  0: "No immediate effect — if you're the only one who played a Spy this round, gain 1 extra favor token at round end.",
  1: "Name a card (not Guard) and choose a player — if they hold it, they're out.",
  2: "Choose a player and secretly look at their hand.",
  3: "Choose a player and compare hands — lower value is out; ties do nothing.",
  4: "You can't be targeted by other players' effects until your next turn.",
  5: "Choose any player (even yourself) to discard their hand and draw a new one.",
  6: "Draw 2 cards, keep 1 of your 3, return the other 2 to the bottom of the deck.",
  7: "Choose a player and trade hands with them.",
  8: "No effect — but you must play her if your other card is the King or a Prince.",
  9: "If you play or discard her for any reason, you're out of the round.",
};
