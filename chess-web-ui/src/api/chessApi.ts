const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:5050/api/game";

export const setPlayerColor = async (color: "white" | "black"): Promise<boolean> => {
    try {
        const res = await fetch(`${API_BASE}/set_player_color`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ color }),
        });
        return res.ok;
    } catch {
        return false;
    }
};

export const getBoard = async (): Promise<{
    board: string;
    turn: "white" | "black";
    is_check: boolean;
    is_checkmate: boolean;
    is_stalemate: boolean;
    is_insufficient_material: boolean;
} | null> => {
    try {
        const res = await fetch(`${API_BASE}/get_board`);
        if (!res.ok) return null;
        return await res.json();
    } catch {
        return null;
    }
};

export const makeMove = async (
    move: string
): Promise<{
    board?: string;
    ai_move?: string;
    turn?: "white" | "black";
    is_check?: boolean;
    is_checkmate?: boolean;
    is_stalemate?: boolean;
    is_insufficient_material?: boolean;
    error?: string;
}> => {
    try {
        const res = await fetch(`${API_BASE}/make_move`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ move: move }),
        });

        const data = await res.json();
        if (!res.ok) {
            return {
                error: data?.error || "Unknown error",
                board: data?.board,
            };
        }

        return data;
    } catch {
        return { error: "Network error" };
    }
};

export const resetBoard = async (): Promise<string | null> => {
    try {
        const res = await fetch(`${API_BASE}/reset`, {
            method: "POST",
        });
        if (!res.ok) return null;
        const data = await res.json();
        return data.board;
    } catch {
        return null;
    }
};

export const startNewGame = async (
    gameType: "ai" | "pvp",
    playerColor: "white" | "black",
    aiStrategy: string = "model"
): Promise<{
    success: boolean;
    board?: string;
    ai_move?: string;
    turn?: string;
}> => {
    try {
        const res = await fetch(`${API_BASE}/start_new_game`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ gameType, playerColor, aiStrategy }),
        });
        if (!res.ok) return { success: false };
        const data = await res.json();
        return { success: true, ...data };
    } catch {
        return { success: false };
    }
};
