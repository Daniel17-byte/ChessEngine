"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "../context/AuthContext";
import { useRouter } from "next/navigation";
import styles from "../styles/Layout.module.css";

interface LayoutProps {
    children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
    const { user, logout, isAuthenticated } = useAuth();
    const router = useRouter();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    const handleLogout = () => {
        logout();
        setMobileMenuOpen(false);
        router.push("/login");
    };

    return (
        <div className={styles.container}>
            <nav className={styles.navbar}>
                <div className={styles.navContent}>
                    <Link href="/" className={styles.logo}>
                        ♟️ Chess Engine
                    </Link>

                    <div className={styles.navLinks}>
                        {isAuthenticated ? (
                            <>
                                <Link href="/play" className={styles.link}>
                                    🎮 Play
                                </Link>
                                <Link href="/leaderboard" className={styles.link}>
                                    🏆 Leaderboard
                                </Link>
                                <Link href="/profile" className={styles.link}>
                                    👤 Profile
                                </Link>
                                <Link href="/admin" className={styles.link}>
                                    ⚙️ Admin
                                </Link>
                                <button onClick={handleLogout} className={styles.logoutBtn}>
                                    Logout
                                </button>
                            </>
                        ) : (
                            <>
                                <Link href="/login" className={styles.link}>
                                    Login
                                </Link>
                                <Link href="/register" className={styles.link}>
                                    Register
                                </Link>
                            </>
                        )}
                    </div>

                    <button
                        className={styles.mobileMenuBtn}
                        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                    >
                        ☰
                    </button>
                </div>

                {mobileMenuOpen && (
                    <div className={styles.mobileMenu}>
                        {isAuthenticated ? (
                            <>
                                <Link href="/play" className={styles.mobileLink}>
                                    🎮 Play
                                </Link>
                                <Link href="/leaderboard" className={styles.mobileLink}>
                                    🏆 Leaderboard
                                </Link>
                                <Link href="/profile" className={styles.mobileLink}>
                                    👤 Profile
                                </Link>
                                <Link href="/admin" className={styles.mobileLink}>
                                    ⚙️ Admin
                                </Link>
                                <button onClick={handleLogout} className={styles.mobileLogoutBtn}>
                                    Logout
                                </button>
                            </>
                        ) : (
                            <>
                                <Link href="/login" className={styles.mobileLink}>
                                    Login
                                </Link>
                                <Link href="/register" className={styles.mobileLink}>
                                    Register
                                </Link>
                            </>
                        )}
                    </div>
                )}
            </nav>

            <main className={styles.main}>
                {children}
            </main>

            <footer className={styles.footer}>
                <p>&copy; 2024 Chess Engine. All rights reserved.</p>
            </footer>
        </div>
    );
};

