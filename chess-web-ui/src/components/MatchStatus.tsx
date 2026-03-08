"use client";

import React from "react";
import { useChess } from "../context/ChessContext";
import styles from "./MatchStatus.module.css";

export const MatchStatus: React.FC = () => {
    const { moveCount, isGameOver, lastAiMove, isCheck } = useChess();

    return (
        <div className={styles.statusBar}>
            <div className={styles.statusItem}>
                <span className={styles.label}>Moves</span>
                <span className={styles.value}>{moveCount}</span>
            </div>

            {lastAiMove && (
                <div className={styles.statusItem}>
                    <span className={styles.label}>AI Move</span>
                    <span className={`${styles.value} ${styles.move}`}>{lastAiMove}</span>
                </div>
            )}

            <div className={styles.statusItem}>
                <span className={styles.label}>Status</span>
                <span className={`${styles.value} ${isGameOver ? styles.gameOver : isCheck ? styles.check : styles.active}`}>
                    {isGameOver ? "🏁 Over" : isCheck ? "⚠️ Check" : "🎮 Playing"}
                </span>
            </div>
        </div>
    );
};
