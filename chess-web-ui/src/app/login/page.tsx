"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../context/AuthContext";
import Link from "next/link";
import styles from "../../styles/Auth.module.css";

export default function LoginPage() {
    const router = useRouter();
    const { login, isLoading, error } = useAuth();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [localError, setLocalError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLocalError(null);

        if (!username || !password) {
            setLocalError("Please fill in all fields");
            return;
        }

        const success = await login({ username, password });
        if (success) {
            router.push("/play");
        } else {
            setLocalError("Login failed. Please check your credentials.");
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.formWrapper}>
                <h1 className={styles.title}>♟️ Chess Engine</h1>
                <h2 className={styles.subtitle}>Login</h2>

                <form onSubmit={handleSubmit} className={styles.form}>
                    <div className={styles.formGroup}>
                        <label htmlFor="username" className={styles.label}>
                            Username
                        </label>
                        <input
                            id="username"
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className={styles.input}
                            placeholder="Enter your username"
                            disabled={isLoading}
                        />
                    </div>

                    <div className={styles.formGroup}>
                        <label htmlFor="password" className={styles.label}>
                            Password
                        </label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className={styles.input}
                            placeholder="Enter your password"
                            disabled={isLoading}
                        />
                    </div>

                    {(error || localError) && (
                        <div className={styles.error}>
                            {error || localError}
                        </div>
                    )}

                    <button
                        type="submit"
                        className={styles.submitBtn}
                        disabled={isLoading}
                    >
                        {isLoading ? "Loading..." : "Login"}
                    </button>
                </form>

                <div className={styles.footer}>
                    <p>
                        Don't have an account?{" "}
                        <Link href="/register" className={styles.link}>
                            Register here
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}

