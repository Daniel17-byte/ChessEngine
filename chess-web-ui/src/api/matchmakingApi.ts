const API_BASE = "http://localhost:8080/api/matches";

export interface Match {
    id: number;
    playerOneId: string;
    playerTwoId?: string;
    status: "PENDING" | "ACTIVE" | "COMPLETED";
    winnerId?: string;
    createdAt: string;
}

export const createMatch = async (playerOneId: string): Promise<Match | null> => {
    try {
        const res = await fetch(`${API_BASE}/create?playerOneId=${playerOneId}`, {
            method: "POST",
            credentials: "include",
        });

        if (!res.ok) return null;
        return await res.json();
    } catch (error) {
        console.error("Create match failed:", error);
        return null;
    }
};

export const joinMatch = async (matchId: number, playerTwoId: string): Promise<Match | null> => {
    try {
        const res = await fetch(`${API_BASE}/join/${matchId}?playerTwoId=${playerTwoId}`, {
            method: "POST",
            credentials: "include",
        });

        if (!res.ok) return null;
        return await res.json();
    } catch (error) {
        console.error("Join match failed:", error);
        return null;
    }
};

export const getAllMatches = async (): Promise<Match[]> => {
    try {
        const res = await fetch(API_BASE, {
            credentials: "include",
        });

        if (!res.ok) return [];
        return await res.json();
    } catch (error) {
        console.error("Get all matches failed:", error);
        return [];
    }
};

