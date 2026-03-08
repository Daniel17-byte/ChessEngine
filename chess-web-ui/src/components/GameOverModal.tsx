"use client";

import React from "react";
import { useChess } from "../context/ChessContext";
import styles from "./GameOverModal.module.css";

interface GameOverModalProps {
    onNewGame: () => void;
}

const resultConfig: Record<string, { emoji: string; title: string; subtitle: string; className: string }> = {
    win: {
        emoji: "🏆",
        title: "Victory!",
        subtitle: "You won the game! Excellent play!",
        className: "win",
    },
    loss: {
        emoji: "😞",
        title: "Defeat",
        subtitle: "You lost this time. Try again!",
        className: "loss",
    },
    draw: {
        emoji: "🤝",
        title: "Draw",
        subtitle: "The game ended in a draw.",
        className: "draw",
    },
};

export const GameOverModal: React.FC<GameOverModalProps> = ({ onNewGame }) => {
    const { gameResult, dismissGameResult, moveCount, isCheckmate, isStalemate } = useChess();

    if (!gameResult) return null;

    const config = resultConfig[gameResult];
    const reason = isCheckmate ? "Checkmate" : isStalemate ? "Stalemate" : "Insufficient material";

    return (
        <div className={styles.overlay} onClick={dismissGameResult}>
            <div className={`${styles.modal} ${styles[config.className]}`} onClick={e => e.stopPropagation()}>
                <div className={styles.emojiContainer}>
                    <span className={styles.emoji}>{config.emoji}</span>
                </div>
                <h2 className={styles.title}>{config.title}</h2>
                <p className={styles.subtitle}>{config.subtitle}</p>
                <div className={styles.details}>
                    <div className={styles.detailItem}>
                        <span className={styles.detailLabel}>Reason</span>
                        <span className={styles.detailValue}>{reason}</span>
                    </div>
                    <div className={styles.detailItem}>
                        <span className={styles.detailLabel}>Moves</span>
                        <span className={styles.detailValue}>{moveCount}</span>
                    </div>
                </div>
                <div className={styles.actions}>
                    <button className={styles.newGameBtn} onClick={onNewGame}>
                        🎮 New Game
                    </button>
                    <button className={styles.closeBtn} onClick={dismissGameResult}>
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

export default GameOverModal;

