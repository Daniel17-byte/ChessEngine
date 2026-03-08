"use client";

import React, { useEffect, useState } from "react";
import { getAllStats, GameStat } from "../../api/statsApi";
import { Layout } from "../../components/Layout";
import { ProtectedRoute } from "../../components/ProtectedRoute";
import styles from "../../styles/Leaderboard.module.css";

interface LeaderboardEntry extends GameStat {
    rank: number;
}

export default function LeaderboardPage() {
    const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const loadStats = async () => {
            setIsLoading(true);
            try {
                const stats = await getAllStats();
                const sorted = [...stats]
                    .sort((a, b) => b.wins - a.wins || b.winRate - a.winRate || a.losses - b.losses);

                const leaderboard: LeaderboardEntry[] = sorted.map((stat, index) => ({
                    ...stat,
                    rank: index + 1,
                }));

                setEntries(leaderboard);
            } catch (error) {
                console.error("Failed to load leaderboard:", error);
            } finally {
                setIsLoading(false);
            }
        };

        loadStats();
    }, []);

    return (
        <ProtectedRoute>
            <Layout>
                <div className={styles.container}>
                    <h1 className={styles.title}>🏆 Leaderboard</h1>

                    {isLoading ? (
                        <div className={styles.loading}>Loading leaderboard...</div>
                    ) : entries.length === 0 ? (
                        <div className={styles.empty}>No players yet. Start playing to appear on the leaderboard!</div>
                    ) : (
                        <div className={styles.tableWrapper}>
                            <table className={styles.table}>
                                <thead>
                                    <tr>
                                        <th className={styles.rankCol}>Rank</th>
                                        <th className={styles.playerCol}>Player</th>
                                        <th className={styles.winsCol}>Wins</th>
                                        <th className={styles.lossesCol}>Losses</th>
                                        <th className={styles.drawsCol}>Draws</th>
                                        <th className={styles.totalCol}>Total</th>
                                        <th className={styles.winRateCol}>Win Rate</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {entries.map((entry) => (
                                        <tr key={entry.userId} className={entry.rank <= 3 ? styles.topThree : ""}>
                                            <td className={styles.rankCol}>
                                                {entry.rank === 1 ? "🥇" : entry.rank === 2 ? "🥈" : entry.rank === 3 ? "🥉" : entry.rank}
                                            </td>
                                            <td className={styles.playerCol}>{entry.userId}</td>
                                            <td className={styles.winsCol}>{entry.wins}</td>
                                            <td className={styles.lossesCol}>{entry.losses}</td>
                                            <td className={styles.drawsCol}>{entry.draws}</td>
                                            <td className={styles.totalCol}>{entry.totalGames}</td>
                                            <td className={styles.winRateCol}>{(entry.winRate * 100).toFixed(1)}%</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </Layout>
        </ProtectedRoute>
    );
}
