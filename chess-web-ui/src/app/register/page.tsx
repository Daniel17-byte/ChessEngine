"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../context/AuthContext";
import Link from "next/link";
import styles from "../../styles/Auth.module.css";

export default function RegisterPage() {
    const router = useRouter();
    const { register, isLoading, error } = useAuth();
    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [localError, setLocalError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLocalError(null);

        if (!username || !email || !password || !confirmPassword) {
            setLocalError("Please fill in all fields");
            return;
        }

        if (password !== confirmPassword) {
            setLocalError("Passwords do not match");
            return;
        }

        if (password.length < 6) {
            setLocalError("Password must be at least 6 characters long");
            return;
        }

        const success = await register({
            username,
            email,
            password,
            color: "white",
        });

        if (success) {
            router.push("/play");
        } else {
            setLocalError("Registration failed. Please try again.");
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.formWrapper}>
                <h1 className={styles.title}>♟️ Chess Engine</h1>
                <h2 className={styles.subtitle}>Register</h2>

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
                            placeholder="Choose a username"
                            disabled={isLoading}
                        />
                    </div>

                    <div className={styles.formGroup}>
                        <label htmlFor="email" className={styles.label}>
                            Email
                        </label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className={styles.input}
                            placeholder="Enter your email"
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

                    <div className={styles.formGroup}>
                        <label htmlFor="confirmPassword" className={styles.label}>
                            Confirm Password
                        </label>
                        <input
                            id="confirmPassword"
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            className={styles.input}
                            placeholder="Confirm your password"
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
                        {isLoading ? "Loading..." : "Register"}
                    </button>
                </form>

                <div className={styles.footer}>
                    <p>
                        Already have an account?{" "}
                        <Link href="/login" className={styles.link}>
                            Login here
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}

