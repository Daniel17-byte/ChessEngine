"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { getPlayerStats, GameStat } from "../../api/statsApi";
import { Layout } from "../../components/Layout";
import { ProtectedRoute } from "../../components/ProtectedRoute";
import styles from "../../styles/Profile.module.css";

export default function ProfilePage() {
    const { user } = useAuth();
    const [stats, setStats] = useState<GameStat | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const loadStats = async () => {
            if (!user?.username) return;
            setIsLoading(true);
            try {
                const playerStats = await getPlayerStats(user.username);
                setStats(playerStats);
            } catch (error) {
                console.error("Failed to load stats:", error);
            } finally {
                setIsLoading(false);
            }
        };

        loadStats();
    }, [user]);

    if (!user) return null;

    return (
        <ProtectedRoute>
            <Layout>
                <div className={styles.container}>
                    <h1 className={styles.title}>👤 Profile</h1>

                    <div className={styles.profileCard}>
                        <div className={styles.header}>
                            <div className={styles.avatar}>👨‍🎮</div>
                            <div className={styles.userInfo}>
                                <h2>{user.username}</h2>
                                {user.email && <p className={styles.email}>{user.email}</p>}
                            </div>
                        </div>

                        {isLoading ? (
                            <div className={styles.loading}>Loading stats...</div>
                        ) : stats ? (
                            <div className={styles.statsGrid}>
                                <div className={styles.statCard}>
                                    <div className={styles.statValue}>{stats.wins}</div>
                                    <div className={styles.statLabel}>🏆 Wins</div>
                                </div>
                                <div className={styles.statCard}>
                                    <div className={styles.statValue}>{stats.losses}</div>
                                    <div className={styles.statLabel}>😞 Losses</div>
                                </div>
                                <div className={styles.statCard}>
                                    <div className={styles.statValue}>{stats.draws}</div>
                                    <div className={styles.statLabel}>🤝 Draws</div>
                                </div>
                                <div className={styles.statCard}>
                                    <div className={styles.statValue}>{stats.totalGames}</div>
                                    <div className={styles.statLabel}>🎮 Total Games</div>
                                </div>
                                <div className={`${styles.statCard} ${styles.winRate}`}>
                                    <div className={styles.statValue}>
                                        {(stats.winRate * 100).toFixed(1)}%
                                    </div>
                                    <div className={styles.statLabel}>📊 Win Rate</div>
                                </div>
                            </div>
                        ) : (
                            <div className={styles.noStats}>
                                No statistics yet. Start playing to see your stats!
                            </div>
                        )}
                    </div>
                </div>
            </Layout>
        </ProtectedRoute>
    );
}
