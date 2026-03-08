"use client";

import React, { useEffect, useState } from "react";
import { getTrainingStatus, startTraining, stopTraining, getStrategies, connectTrainingSocket, startEloEstimation, stopEloEstimation, getEloStatus, connectEloSocket } from "../../api/adminApi";
import type { TrainingStatus, TrainingStrategy, EloStatus } from "../../api/adminApi";
import { Layout } from "../../components/Layout";
import { ProtectedRoute } from "../../components/ProtectedRoute";
import styles from "../../styles/Admin.module.css";

export default function AdminPage() {
    const [strategies, setStrategies] = useState<TrainingStrategy[]>([]);
    const [selectedStrategy, setSelectedStrategy] = useState<string>("mirror_match");
    const [epochs, setEpochs] = useState<number>(100);
    const [maxMoves, setMaxMoves] = useState<number>(80);
    const [whiteStrategy, setWhiteStrategy] = useState<string>("model");
    const [blackStrategy, setBlackStrategy] = useState<string>("model");
    const [fenType, setFenType] = useState<string>("endgames");
    const [trainingStatus, setTrainingStatus] = useState<TrainingStatus | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [gameDetails, setGameDetails] = useState<any>(null);

    // ELO estimation state
    const [eloStatus, setEloStatus] = useState<EloStatus | null>(null);
    const [eloGamesPerLevel, setEloGamesPerLevel] = useState<number>(20);
    const [eloMaxLevel, setEloMaxLevel] = useState<number>(10);

    // ... existing code ...

    // Fetch strategies on mount
    useEffect(() => {
        const loadStrategies = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const data = await getStrategies();
                if (data && data.length > 0) {
                    setStrategies(data);
                    setSelectedStrategy(data[0].id);
                    setEpochs(data[0].recommended_epochs);
                } else {
                    setError("No training strategies available");
                }
            } catch (err) {
                console.error("Failed to load strategies:", err);
                setError("Failed to load training strategies. Make sure AI engine is running on port 5050.");
            } finally {
                setIsLoading(false);
            }
        };
        loadStrategies();
    }, []);

    // Real-time training status via WebSocket
    useEffect(() => {
        if (isLoading) return; // Wait for strategies to load first

        // Fetch initial status via REST
        const loadInitial = async () => {
            try {
                const status = await getTrainingStatus();
                if (status) {
                    setTrainingStatus(status);
                    const details = parseGameDetails(status.current_status);
                    setGameDetails(details);
                }
            } catch (err) {
                console.error("Failed to fetch initial training status:", err);
            }
        };
        loadInitial();

        // Connect WebSocket for live updates
        const disconnect = connectTrainingSocket((status) => {
            setTrainingStatus(status);
            const details = parseGameDetails(status.current_status);
            setGameDetails(details);
        });

        return () => {
            disconnect();
        };
    }, [isLoading]);

    // ELO estimation WebSocket
    useEffect(() => {
        if (isLoading) return;

        const loadElo = async () => {
            const status = await getEloStatus();
            if (status) setEloStatus(status);
        };
        loadElo();

        const disconnectElo = connectEloSocket((status) => {
            setEloStatus(status);
        });

        return () => { disconnectElo(); };
    }, [isLoading]);

    const handleStartElo = async () => {
        await startEloEstimation(eloGamesPerLevel, eloMaxLevel);
    };

    const handleStopElo = async () => {
        await stopEloEstimation();
    };

    const handleStartTraining = async () => {
        const success = await startTraining(
            selectedStrategy,
            epochs,
            maxMoves,
            selectedStrategy === "mirror_match" ? whiteStrategy : "model",
            selectedStrategy === "mirror_match" ? blackStrategy : "model",
            selectedStrategy === "mirror_match" ? fenType : "endgames"
        );
        if (success) {
            const status = await getTrainingStatus();
            setTrainingStatus(status);
        }
    };

    const handleStopTraining = async () => {
        const success = await stopTraining();
        if (success) {
            const status = await getTrainingStatus();
            setTrainingStatus(status);
        }
    };

    // Parse game details from status message
    const parseGameDetails = (statusMsg: string) => {
        if (!statusMsg) return null;

        try {
            const details: any = {};

            // Parse winner
            if (statusMsg.includes("White Wins")) {
                details.winner = "White";
                details.whiteReward = 10.0;
                details.blackReward = -10.0;
            } else if (statusMsg.includes("Black Wins")) {
                details.winner = "Black";
                details.whiteReward = -10.0;
                details.blackReward = 10.0;
            } else if (statusMsg.includes("Draw")) {
                details.winner = "Draw";
                details.whiteReward = 0.0;
                details.blackReward = 0.0;
            }

            // Parse move count
            const movesMatch = statusMsg.match(/Moves: (\d+)/);
            details.moves = movesMatch ? parseInt(movesMatch[1]) : 0;

            // Parse loss
            const lossMatch = statusMsg.match(/Loss: ([\d.]+)/);
            details.loss = lossMatch ? parseFloat(lossMatch[1]) : 0;

            // Parse epochs
            const epochMatch = statusMsg.match(/Epoch (\d+)\/(\d+)/);
            if (epochMatch) {
                details.epoch = parseInt(epochMatch[1]);
                details.maxEpochs = parseInt(epochMatch[2]);
            }

            return Object.keys(details).length > 0 ? details : null;
        } catch (err) {
            return null;
        }
    };

    const selectedStrategyData = strategies.find(s => s.id === selectedStrategy);
    const progress = trainingStatus?.max_epochs ? (trainingStatus.epochs / trainingStatus.max_epochs) * 100 : 0;

    return (
        <ProtectedRoute>
            <Layout>
                <div className={styles.container}>
                    <h1 className={styles.title}>⚙️ Admin Panel - Model Training</h1>

                    {error && (
                        <div className={styles.errorBanner}>
                            <strong>❌ Error:</strong> {error}
                        </div>
                    )}

                    <div className={styles.grid}>
                        {/* Left Column - Training Configuration */}
                        <div className={styles.configPanel}>
                            <h2 className={styles.sectionTitle}>🎯 Training Configuration</h2>

                            {isLoading ? (
                                <div className={styles.loading}>Loading strategies...</div>
                            ) : (
                                <div className={styles.configForm}>
                                    {/* Strategy Selection */}
                                    <div className={styles.formGroup}>
                                        <label className={styles.label}>Select Training Strategy</label>
                                        <select
                                            value={selectedStrategy}
                                            onChange={(e) => {
                                                setSelectedStrategy(e.target.value);
                                                const strategy = strategies.find(s => s.id === e.target.value);
                                                if (strategy) setEpochs(strategy.recommended_epochs);
                                            }}
                                            disabled={trainingStatus?.is_training}
                                            className={styles.select}
                                        >
                                            {strategies.map(s => (
                                                <option key={s.id} value={s.id}>
                                                    {s.name} - {s.description}
                                                </option>
                                            ))}
                                        </select>
                                    </div>

                                    {/* Strategy Description */}
                                    {selectedStrategyData && (
                                        <div className={styles.description}>
                                            <h3>{selectedStrategyData.name}</h3>
                                            <p>{selectedStrategyData.description}</p>
                                            <p className={styles.recommended}>
                                                Recommended epochs: {selectedStrategyData.recommended_epochs}
                                            </p>
                                        </div>
                                    )}

                                    {/* Epochs Input */}
                                    <div className={styles.formGroup}>
                                        <label className={styles.label}>Number of Epochs</label>
                                        <input
                                            type="number"
                                            min="1"
                                            max="1000"
                                            value={epochs}
                                            onChange={(e) => setEpochs(Math.max(1, parseInt(e.target.value) || 1))}
                                            disabled={trainingStatus?.is_training}
                                            className={styles.input}
                                        />
                                    </div>

                                    {/* Max Moves Input - only for Mirror Match */}
                                    {selectedStrategy === "mirror_match" && (
                                    <div className={styles.formGroup}>
                                        <label className={styles.label}>Max Moves Per Game</label>
                                        <input
                                            type="number"
                                            min="10"
                                            max="500"
                                            value={maxMoves}
                                            onChange={(e) => setMaxMoves(Math.max(10, parseInt(e.target.value) || 80))}
                                            disabled={trainingStatus?.is_training}
                                            className={styles.input}
                                        />
                                    </div>
                                    )}

                                    {/* White Strategy Selection (only for Mirror Match) */}
                                    {selectedStrategy === "mirror_match" && (
                                        <div className={styles.formGroup}>
                                            <label className={styles.label}>White Strategy</label>
                                            <select
                                                value={whiteStrategy}
                                                onChange={(e) => setWhiteStrategy(e.target.value)}
                                                disabled={trainingStatus?.is_training}
                                                className={styles.select}
                                            >
                                                <option value="model">🧠 Danibot</option>
                                                <option value="random">Random</option>
                                                <option value="stockfish">Stockfish Engine</option>
                                            </select>
                                        </div>
                                    )}

                                    {/* Black Strategy Selection (only for Mirror Match) */}
                                    {selectedStrategy === "mirror_match" && (
                                        <div className={styles.formGroup}>
                                            <label className={styles.label}>Black Strategy</label>
                                            <select
                                                value={blackStrategy}
                                                onChange={(e) => setBlackStrategy(e.target.value)}
                                                disabled={trainingStatus?.is_training}
                                                className={styles.select}
                                            >
                                                <option value="model">🧠 Danibot</option>
                                                <option value="random">Random</option>
                                                <option value="stockfish">Stockfish Engine</option>
                                            </select>
                                        </div>
                                    )}

                                    {/* FEN Type Selection (only for Mirror Match) */}
                                    {selectedStrategy === "mirror_match" && (
                                        <div className={styles.formGroup}>
                                            <label className={styles.label}>Training Positions</label>
                                            <select
                                                value={fenType}
                                                onChange={(e) => setFenType(e.target.value)}
                                                disabled={trainingStatus?.is_training}
                                                className={styles.select}
                                            >
                                                <option value="endgames">Endgame Positions</option>
                                                <option value="normal_games">Normal Games</option>
                                                <option value="mixed">Mixed Positions</option>
                                            </select>
                                        </div>
                                    )}

                                    {/* Control Buttons */}
                                    <div className={styles.buttonGroup}>
                                        <button
                                            onClick={handleStartTraining}
                                            disabled={trainingStatus?.is_training || isLoading}
                                            className={`${styles.btn} ${styles.startBtn}`}
                                        >
                                            ▶️ Start Training
                                        </button>
                                        <button
                                            onClick={handleStopTraining}
                                            disabled={!trainingStatus?.is_training}
                                            className={`${styles.btn} ${styles.stopBtn}`}
                                        >
                                            ⏹️ Stop Training
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Right Column - Training Status */}
                        <div className={styles.statusPanel}>
                            <h2 className={styles.sectionTitle}>📊 Training Status</h2>

                            {trainingStatus ? (
                                <div className={styles.statusContent}>
                                    {/* Status Badge */}
                                    <div className={`${styles.badge} ${trainingStatus.is_training ? styles.active : styles.inactive}`}>
                                        {trainingStatus.is_training ? "🔴 TRAINING" : "⚪ IDLE"}
                                    </div>

                                    {/* Current Status */}
                                    <div className={styles.statusItem}>
                                        <span className={styles.label}>Status:</span>
                                        <span className={styles.value}>{trainingStatus.current_status}</span>
                                    </div>

                                    {/* Progress Bar */}
                                    {trainingStatus.is_training && (
                                        <div className={styles.progressContainer}>
                                            <div className={styles.progressLabel}>
                                                Epoch {trainingStatus.epochs} / {trainingStatus.max_epochs}
                                            </div>
                                            <div className={styles.progressBar}>
                                                <div
                                                    className={styles.progressFill}
                                                    style={{ width: `${progress}%` }}
                                                />
                                            </div>
                                            <div className={styles.progressPercent}>{progress.toFixed(1)}%</div>
                                        </div>
                                    )}

                                    {/* Stats Grid */}
                                    <div className={styles.statsGrid}>
                                        <div className={styles.statItem}>
                                            <div className={styles.statLabel}>Games Played</div>
                                            <div className={styles.statValue}>{trainingStatus.games_played}</div>
                                        </div>
                                        <div className={styles.statItem}>
                                            <div className={styles.statLabel}>Loss Value</div>
                                            <div className={styles.statValue}>{trainingStatus.loss_value.toFixed(4)}</div>
                                        </div>
                                        <div className={styles.statItem}>
                                            <div className={styles.statLabel}>Accuracy</div>
                                            <div className={styles.statValue}>{trainingStatus.accuracy?.toFixed(1) ?? "0.0"}%</div>
                                        </div>
                                        <div className={styles.statItem}>
                                            <div className={styles.statLabel}>White Wins</div>
                                            <div className={styles.statValue}>{trainingStatus.wins_white}</div>
                                        </div>
                                        <div className={styles.statItem}>
                                            <div className={styles.statLabel}>Black Wins</div>
                                            <div className={styles.statValue}>{trainingStatus.wins_black}</div>
                                        </div>
                                        <div className={styles.statItem}>
                                            <div className={styles.statLabel}>Draws</div>
                                            <div className={styles.statValue}>{trainingStatus.draws}</div>
                                        </div>
                                        <div className={styles.statItem}>
                                            <div className={styles.statLabel}>Strategy</div>
                                            <div className={styles.statValue}>{trainingStatus.strategy || "N/A"}</div>
                                        </div>
                                    </div>

                                    {/* Game Result Details */}
                                    {trainingStatus.is_training && gameDetails && (
                                        <div className={styles.gameResultContainer}>
                                            <h3 className={styles.gameResultTitle}>🎯 Latest Game Result</h3>
                                            <div className={styles.gameResultContent}>
                                                {gameDetails.winner === "White" && (
                                                    <div className={styles.winnerCard}>
                                                        <div className={styles.winnerBadge}>🏳️ WHITE WINS</div>
                                                        <div className={styles.gameMetrics}>
                                                            <div className={styles.metricRow}>
                                                                <span>Moves:</span>
                                                                <span className={styles.metricValue}>{gameDetails.moves}</span>
                                                            </div>
                                                            <div className={styles.metricRow}>
                                                                <span>Loss:</span>
                                                                <span className={styles.metricValue}>{gameDetails.loss.toFixed(4)}</span>
                                                            </div>
                                                        </div>
                                                        <div className={styles.rewardRow}>
                                                            <span className={styles.playerLabel}>⚪ White Reward:</span>
                                                            <span className={`${styles.reward} ${styles.positive}`}>+10.00</span>
                                                        </div>
                                                        <div className={styles.rewardRow}>
                                                            <span className={styles.playerLabel}>⚫ Black Reward:</span>
                                                            <span className={`${styles.reward} ${styles.negative}`}>-10.00</span>
                                                        </div>
                                                    </div>
                                                )}
                                                {gameDetails.winner === "Black" && (
                                                    <div className={styles.winnerCard}>
                                                        <div className={`${styles.winnerBadge} ${styles.blackWins}`}>🏳️ BLACK WINS</div>
                                                        <div className={styles.gameMetrics}>
                                                            <div className={styles.metricRow}>
                                                                <span>Moves:</span>
                                                                <span className={styles.metricValue}>{gameDetails.moves}</span>
                                                            </div>
                                                            <div className={styles.metricRow}>
                                                                <span>Loss:</span>
                                                                <span className={styles.metricValue}>{gameDetails.loss.toFixed(4)}</span>
                                                            </div>
                                                        </div>
                                                        <div className={styles.rewardRow}>
                                                            <span className={styles.playerLabel}>⚪ White Reward:</span>
                                                            <span className={`${styles.reward} ${styles.negative}`}>-10.00</span>
                                                        </div>
                                                        <div className={styles.rewardRow}>
                                                            <span className={styles.playerLabel}>⚫ Black Reward:</span>
                                                            <span className={`${styles.reward} ${styles.positive}`}>+10.00</span>
                                                        </div>
                                                    </div>
                                                )}
                                                {gameDetails.winner === "Draw" && (
                                                    <div className={styles.winnerCard}>
                                                        <div className={`${styles.winnerBadge} ${styles.draw}`}>🤝 DRAW</div>
                                                        <div className={styles.gameMetrics}>
                                                            <div className={styles.metricRow}>
                                                                <span>Moves:</span>
                                                                <span className={styles.metricValue}>{gameDetails.moves}</span>
                                                            </div>
                                                            <div className={styles.metricRow}>
                                                                <span>Loss:</span>
                                                                <span className={styles.metricValue}>{gameDetails.loss.toFixed(4)}</span>
                                                            </div>
                                                        </div>
                                                        <div className={styles.rewardRow}>
                                                            <span className={styles.playerLabel}>⚪ White Reward:</span>
                                                            <span className={styles.reward}>±0.00</span>
                                                        </div>
                                                        <div className={styles.rewardRow}>
                                                            <span className={styles.playerLabel}>⚫ Black Reward:</span>
                                                            <span className={styles.reward}>±0.00</span>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className={styles.loading}>Loading status...</div>
                            )}
                        </div>
                    </div>

                    {/* ELO Estimation Section */}
                    <div className={styles.section}>
                        <h2 className={styles.sectionTitle}>🧠 Danibot ELO Estimation</h2>
                        <div className={styles.card}>
                            <div className={styles.formRow} style={{ display: "flex", gap: "1rem", alignItems: "flex-end", flexWrap: "wrap" }}>
                                <div className={styles.formGroup} style={{ flex: 1, minWidth: "120px" }}>
                                    <label className={styles.label}>Games per Level</label>
                                    <input
                                        type="number"
                                        min="2"
                                        max="100"
                                        value={eloGamesPerLevel}
                                        onChange={(e) => setEloGamesPerLevel(Math.max(2, parseInt(e.target.value) || 20))}
                                        disabled={eloStatus?.is_running}
                                        className={styles.input}
                                    />
                                </div>
                                <div className={styles.formGroup} style={{ flex: 1, minWidth: "120px" }}>
                                    <label className={styles.label}>Max Stockfish Level</label>
                                    <input
                                        type="number"
                                        min="1"
                                        max="20"
                                        value={eloMaxLevel}
                                        onChange={(e) => setEloMaxLevel(Math.max(1, parseInt(e.target.value) || 10))}
                                        disabled={eloStatus?.is_running}
                                        className={styles.input}
                                    />
                                </div>
                                <div style={{ flex: 1, minWidth: "120px", display: "flex", alignItems: "flex-end" }}>
                                    {!eloStatus?.is_running ? (
                                        <button onClick={handleStartElo} className={`${styles.btn} ${styles.startBtn}`} style={{ width: "100%", margin: 0 }}>
                                            🧪 Estimate ELO
                                        </button>
                                    ) : (
                                        <button onClick={handleStopElo} className={`${styles.btn} ${styles.stopBtn}`} style={{ width: "100%", margin: 0 }}>
                                            ⏹ Stop Estimation
                                        </button>
                                    )}
                                </div>
                            </div>

                            {/* ELO Status */}
                            {eloStatus && eloStatus.status !== "idle" && (
                                <div style={{ marginTop: "1rem" }}>
                                    <p className={styles.statusText} style={{ marginBottom: "0.5rem" }}>
                                        {eloStatus.status}
                                    </p>

                                    {/* Estimated ELO Badge */}
                                    {eloStatus.estimated_elo && (
                                        <div style={{
                                            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                                            color: "white",
                                            padding: "1rem 1.5rem",
                                            borderRadius: "12px",
                                            textAlign: "center",
                                            marginBottom: "1rem",
                                            fontSize: "1.2rem",
                                            fontWeight: "bold"
                                        }}>
                                            🧠 Danibot ELO: {eloStatus.estimated_elo}
                                        </div>
                                    )}

                                    {/* Results Table */}
                                    {Object.keys(eloStatus.results).length > 0 && (
                                        <div style={{ overflowX: "auto" }}>
                                            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                                                <thead>
                                                    <tr style={{ borderBottom: "2px solid #444" }}>
                                                        <th style={{ padding: "6px 8px", textAlign: "left" }}>Level</th>
                                                        <th style={{ padding: "6px 8px", textAlign: "center" }}>ELO</th>
                                                        <th style={{ padding: "6px 8px", textAlign: "center" }}>W</th>
                                                        <th style={{ padding: "6px 8px", textAlign: "center" }}>D</th>
                                                        <th style={{ padding: "6px 8px", textAlign: "center" }}>L</th>
                                                        <th style={{ padding: "6px 8px", textAlign: "left" }}>Win Rate</th>
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {Object.entries(eloStatus.results)
                                                        .sort(([a], [b]) => parseInt(a) - parseInt(b))
                                                        .map(([level, data]) => {
                                                            const wr = data.win_rate * 100;
                                                            const barWidth = Math.round(wr);
                                                            const barColor = wr >= 50 ? "#4ade80" : wr >= 25 ? "#facc15" : "#f87171";
                                                            return (
                                                                <tr key={level} style={{ borderBottom: "1px solid #333" }}>
                                                                    <td style={{ padding: "6px 8px" }}>L{level}</td>
                                                                    <td style={{ padding: "6px 8px", textAlign: "center" }}>~{data.elo}</td>
                                                                    <td style={{ padding: "6px 8px", textAlign: "center", color: "#4ade80" }}>{data.wins}</td>
                                                                    <td style={{ padding: "6px 8px", textAlign: "center", color: "#94a3b8" }}>{data.draws}</td>
                                                                    <td style={{ padding: "6px 8px", textAlign: "center", color: "#f87171" }}>{data.losses}</td>
                                                                    <td style={{ padding: "6px 8px" }}>
                                                                        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                                                                            <div style={{
                                                                                width: "80px", height: "10px",
                                                                                background: "#333", borderRadius: "5px", overflow: "hidden"
                                                                            }}>
                                                                                <div style={{
                                                                                    width: `${barWidth}%`, height: "100%",
                                                                                    background: barColor, borderRadius: "5px"
                                                                                }} />
                                                                            </div>
                                                                            <span>{wr.toFixed(0)}%</span>
                                                                        </div>
                                                                    </td>
                                                                </tr>
                                                            );
                                                        })}
                                                </tbody>
                                            </table>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Info Section */}
                    <div className={styles.infoSection}>
                        <h2 className={styles.sectionTitle}>ℹ️ About Training Strategies</h2>
                        <div className={styles.infoGrid}>
                            <div className={styles.infoCard}>
                                <h3>🔄 Mirror Match</h3>
                                <p>Two identical models play against each other. Great for general improvement and avoiding overfitting.</p>
                            </div>
                            <div className={styles.infoCard}>
                                <h3>♞ Stockfish Trainer</h3>
                                <p>Model learns by playing against Stockfish engine. Best for learning strong tactical patterns.</p>
                            </div>
                            <div className={styles.infoCard}>
                                <h3>🎓 Archive Alpha</h3>
                                <p>Model learns from a database of real games (Lichess). Trains on thousands of human positions — the most data-efficient strategy.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </Layout>
        </ProtectedRoute>
    );
}

