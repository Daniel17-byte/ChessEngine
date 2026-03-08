const API_BASE = "http://localhost:8080/api/users";

export interface User {
    uuid?: string;
    username: string;
    email?: string;
    password?: string;
}

export interface LoginCredentials {
    username: string;
    password: string;
}

export const register = async (user: User): Promise<User | null> => {
    try {
        const res = await fetch(`${API_BASE}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(user),
            credentials: "include",
        });

        if (!res.ok) {
            const error = await res.json();
            console.error("Registration error:", error);
            return null;
        }

        return await res.json();
    } catch (error) {
        console.error("Registration failed:", error);
        return null;
    }
};

export const login = async (credentials: LoginCredentials): Promise<User | null> => {
    try {
        const res = await fetch(`${API_BASE}/authenticate`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(credentials),
            credentials: "include",
        });

        if (!res.ok) {
            console.error("Login failed with status:", res.status);
            return null;
        }

        return await res.json();
    } catch (error) {
        console.error("Login failed:", error);
        return null;
    }
};

export const logout = (): void => {
    sessionStorage.removeItem("user");
    sessionStorage.removeItem("token");
};

export const getCurrentUser = async (username: string): Promise<User | null> => {
    try {
        const res = await fetch(`${API_BASE}/username/${username}`, {
            credentials: "include",
        });

        if (!res.ok) return null;
        return await res.json();
    } catch (error) {
        console.error("Get user failed:", error);
        return null;
    }
};

export const getAllUsers = async (): Promise<User[]> => {
    try {
        const res = await fetch(`${API_BASE}`, {
            credentials: "include",
        });

        if (!res.ok) return [];
        return await res.json();
    } catch (error) {
        console.error("Get all users failed:", error);
        return [];
    }
};

