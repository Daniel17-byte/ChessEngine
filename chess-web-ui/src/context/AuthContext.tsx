"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { login, register, logout, User as ApiUser, LoginCredentials } from "../api/authApi";

interface User extends ApiUser {
    color: "white" | "black";
}

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    error: string | null;
    login: (credentials: LoginCredentials) => Promise<boolean>;
    register: (user: User) => Promise<boolean>;
    logout: () => void;
    isBoardFlipped: boolean; // Added to context
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isBoardFlipped, setIsBoardFlipped] = useState(false);

    useEffect(() => {
        const storedUser = sessionStorage.getItem("user");
        if (storedUser) {
            try {
                setUser(JSON.parse(storedUser));
            } catch (e) {
                console.error("Failed to parse stored user:", e);
                sessionStorage.removeItem("user");
            }
        }
        setIsLoading(false);
    }, []);

    useEffect(() => {
        if (user && user.color === "black") {
            setIsBoardFlipped(true);
        } else {
            setIsBoardFlipped(false);
        }
    }, [user]);

    const handleLogin = async (credentials: LoginCredentials): Promise<boolean> => {
        setIsLoading(true);
        setError(null);
        try {
            const userData = await login(credentials);
            if (userData) {
                const userWithColor = { ...userData, color: "white" as "white" | "black" }; // Explicitly cast color
                setUser(userWithColor);
                sessionStorage.setItem("user", JSON.stringify(userWithColor));
                return true;
            } else {
                setError("Invalid username or password");
                return false;
            }
        } catch (err) {
            setError("Login failed");
            console.error("Login error:", err);
            return false;
        } finally {
            setIsLoading(false);
        }
    };

    const handleRegister = async (userData: User): Promise<boolean> => {
        setIsLoading(true);
        setError(null);
        try {
            const newUser = await register(userData);
            if (newUser) {
                const userWithColor = { ...newUser, color: "white" as "white" | "black" }; // Explicitly cast color
                setUser(userWithColor);
                sessionStorage.setItem("user", JSON.stringify(userWithColor));
                return true;
            } else {
                setError("Registration failed");
                return false;
            }
        } catch (err) {
            setError("Registration failed");
            console.error("Registration error:", err);
            return false;
        } finally {
            setIsLoading(false);
        }
    };

    const handleLogout = () => {
        logout();
        setUser(null);
        sessionStorage.removeItem("user");
    };

    const handleStartGame = async () => {
        try {
            const response = await fetch("/api/game/start_new_game", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    playerColor: user?.color || "white",
                    gameType: "ai", // Example, adjust as needed
                }),
            });

            if (response.ok) {
                const data = await response.json();
                setBoard(data.board); // Update board immediately after starting a new game

                // Automatically flip the board if the user is black
                if (user?.color === "black") {
                    setIsBoardFlipped(true);
                } else {
                    setIsBoardFlipped(false);
                }
            } else {
                console.error("Failed to start new game");
            }
        } catch (error) {
            console.error("Error starting new game:", error);
        }
    };

    // Define setBoard function to reset the board
    const setBoard = (board: string) => {
        console.log("Board reset to:", board);
        // Implement board reset logic here
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                isLoading,
                isAuthenticated: !!user,
                error,
                login: handleLogin,
                register: handleRegister,
                logout: handleLogout,
                isBoardFlipped, // Added to context
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = (): AuthContextType => {
    const context = useContext(AuthContext);
    if (!context) throw new Error("useAuth must be used within AuthProvider");
    return context;
};

// Modify the User type inline to include the color property
interface User {
    color: "white" | "black";
    // ...existing properties
}
