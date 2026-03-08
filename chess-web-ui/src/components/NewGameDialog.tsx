"use client";

import React, { useState } from "react";
import { useChess, GameType, PlayerColor, AiOpponent } from "../context/ChessContext";
import { startNewGame } from "../api/chessApi";
import styles from "./NewGameDialog.module.css";

interface NewGameDialogProps {
    isOpen: boolean;
    onClose: () => void;
}

const NewGameDialog: React.FC<NewGameDialogProps> = ({ isOpen, onClose }) => {
    const { setGameSettings, setFen, setLastAiMove } = useChess();
    const [selectedGameType, setSelectedGameType] = useState<GameType>(GameType.AI);
    const [selectedColor, setSelectedColor] = useState<PlayerColor>(PlayerColor.WHITE);
    const [selectedOpponent, setSelectedOpponent] = useState<AiOpponent>(AiOpponent.DANIBOT);
    const [isLoading, setIsLoading] = useState(false);

    const backendPlayerColor = selectedColor === PlayerColor.WHITE ? "white" : "black";

    const handleStartGame = async () => {
        setIsLoading(true);
        try {
            const responseData = await startNewGame(
                selectedGameType,
                backendPlayerColor,
                selectedOpponent
            );

            if (!responseData.success) {
                console.error("Failed to start game on backend");
                return;
            }

            setGameSettings(selectedGameType, selectedColor, selectedOpponent);

            if (responseData.board) {
                setFen(responseData.board);
            }
            if (responseData.ai_move) {
                setLastAiMove(responseData.ai_move);
            }

            onClose();
        } catch (error) {
            console.error("Error starting game:", error);
        } finally {
            setIsLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className={styles.overlay}>
            <div className={styles.dialog}>
                <h2>🎮 New Game</h2>

                <div className={styles.section}>
                    <h3>Choose Your Color</h3>
                    <div className={styles.colorOptions}>
                        <button
                            className={`${styles.colorBtn} ${selectedColor === PlayerColor.WHITE ? styles.selected : ""}`}
                            onClick={() => setSelectedColor(PlayerColor.WHITE)}
                            disabled={isLoading}
                        >
                            ♔ White
                        </button>
                        <button
                            className={`${styles.colorBtn} ${selectedColor === PlayerColor.BLACK ? styles.selected : ""}`}
                            onClick={() => setSelectedColor(PlayerColor.BLACK)}
                            disabled={isLoading}
                        >
                            ♚ Black
                        </button>
                    </div>
                </div>

                <div className={styles.section}>
                    <h3>Choose Opponent</h3>
                    <div className={styles.opponentOptions}>
                        <button
                            className={`${styles.opponentBtn} ${selectedGameType === GameType.AI ? styles.selected : ""}`}
                            onClick={() => setSelectedGameType(GameType.AI)}
                            disabled={isLoading}
                        >
                            🤖 Play vs AI
                        </button>
                        <button
                            className={`${styles.opponentBtn} ${selectedGameType === GameType.PVP ? styles.selected : ""}`}
                            onClick={() => setSelectedGameType(GameType.PVP)}
                            disabled={isLoading}
                        >
                            👥 Play vs Player (Coming Soon)
                        </button>
                    </div>
                </div>

                {/* AI Opponent Selection — only shown when AI is selected */}
                {selectedGameType === GameType.AI && (
                    <div className={styles.section}>
                        <h3>Choose AI Engine</h3>
                        <div className={styles.opponentOptions}>
                            <button
                                className={`${styles.aiBtn} ${selectedOpponent === AiOpponent.DANIBOT ? styles.selectedDanibot : ""}`}
                                onClick={() => setSelectedOpponent(AiOpponent.DANIBOT)}
                                disabled={isLoading}
                            >
                                <span className={styles.aiBtnIcon}>🧠</span>
                                <span className={styles.aiBtnName}>Danibot</span>
                                <span className={styles.aiBtnDesc}>Custom Neural Network</span>
                            </button>
                            <button
                                className={`${styles.aiBtn} ${selectedOpponent === AiOpponent.STOCKFISH ? styles.selectedStockfish : ""}`}
                                onClick={() => setSelectedOpponent(AiOpponent.STOCKFISH)}
                                disabled={isLoading}
                            >
                                <span className={styles.aiBtnIcon}>♞</span>
                                <span className={styles.aiBtnName}>Stockfish</span>
                                <span className={styles.aiBtnDesc}>World-class Engine</span>
                            </button>
                        </div>
                    </div>
                )}

                <div className={styles.actions}>
                    <button
                        className={styles.startBtn}
                        onClick={handleStartGame}
                        disabled={isLoading}
                    >
                        {isLoading ? "⏳ Starting..." : "▶️ Start Game"}
                    </button>
                    <button
                        className={styles.cancelBtn}
                        onClick={onClose}
                        disabled={isLoading}
                    >
                        ✕ Cancel
                    </button>
                </div>
            </div>
        </div>
    );
};

export default NewGameDialog;

