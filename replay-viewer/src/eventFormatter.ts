/**
 * Format replay events into human-readable descriptions
 */

import type { ReplayEvent, CardType } from "./types";

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text: string): string {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Format card type for display
 */
function formatCard(card: CardType): string {
  return card
    .split("_")
    .map((word) => word.charAt(0) + word.slice(1).toLowerCase())
    .join(" ");
}

/**
 * Format a replay event into a human-readable description
 */
export function formatEvent(event: ReplayEvent, index: number): string {
  const escaped = (text: string) => escapeHtml(text);

  switch (event.type) {
    case "game_setup":
      return `<strong>Game Setup</strong> - ${event.play_order
        .map(escaped)
        .join(", ")}`;

    case "turn_start":
      return `<strong>Turn ${event.turn_number}:</strong> ${escaped(
        event.player
      )}'s turn (${event.turns_remaining} turn${
        event.turns_remaining > 1 ? "s" : ""
      } remaining)`;

    case "card_play":
      return `${escaped(event.player)} plays <em>${formatCard(
        event.card
      )}</em>`;

    case "combo_play":
      const cards = event.cards.map(formatCard).join(", ");
      const target = event.target ? ` targeting ${escaped(event.target)}` : "";
      return `${escaped(event.player)} plays <strong>${
        event.combo_type
      }</strong> combo${target}`;

    case "nope":
      const originalAction = event.original_action || event.action;
      const targetPlayer = event.target_player
        ? ` from ${escaped(event.target_player)}`
        : "";
      return `🚫 ${escaped(event.player)} plays <strong>NOPE</strong>${targetPlayer}`;

    case "card_draw":
      return `${escaped(event.player)} draws <em>${formatCard(
        event.card
      )}</em>`;

    case "exploding_kitten_draw":
      if (event.had_defuse) {
        return `💣 ${escaped(
          event.player
        )} draws Exploding Kitten but has Defuse!`;
      }
      return `💀 ${escaped(event.player)} draws Exploding Kitten and EXPLODES!`;

    case "defuse":
      return `${escaped(
        event.player
      )} defuses and inserts kitten at position ${event.insert_position}`;

    case "player_elimination":
      return `💀 ${escaped(event.player)} is eliminated`;

    case "see_future":
      const cardsSeen = event.cards_seen.map(formatCard).join(", ");
      return `${escaped(event.player)} sees the future: ${cardsSeen}`;

    case "shuffle":
      return `${escaped(event.player)} shuffles the deck`;

    case "favor":
      return `${escaped(event.player)} asks favor from ${escaped(
        event.target
      )}`;

    case "card_steal":
      return `${escaped(event.thief)} steals a card from ${escaped(
        event.victim
      )}`;

    case "card_request":
      const success = event.success ? "✓" : "✗";
      return `${success} ${escaped(event.requester)} requests <em>${formatCard(
        event.requested_card
      )}</em> from ${escaped(event.target)}`;

    case "discard_take":
      return `${escaped(event.player)} takes <em>${formatCard(
        event.card
      )}</em> from discard`;

    case "game_end":
      const winner = event.winner ? escaped(event.winner) : "No one";
      return `🎉 <strong>Game Over!</strong> Winner: ${winner}`;

    default:
      return `Unknown event type`;
  }
}
