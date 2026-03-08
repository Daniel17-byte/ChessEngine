"use client";

import React, { useState, useRef, useCallback } from "react";
import styles from "./ChessBoard.module.css";
import { useChess } from "../context/ChessContext";

const pieceSymbols: Record<string, string> = {
    P: "♙", N: "♘", B: "♗", R: "♖", Q: "♕", K: "♔",
    p: "♟", n: "♞", b: "♝", r: "♜", q: "♛", k: "♚",
};

function parseFEN(fen: string): string[][] {
    const board: string[][] = [];
    const rows = (fen ?? "").split(" ")[0].split("/");
    for (const row of rows) {
        const cells: string[] = [];
        for (const char of row) {
            if (isNaN(parseInt(char))) {
                cells.push(char);
            } else {
                cells.push(...Array(parseInt(char)).fill(""));
            }
        }
        board.push(cells);
    }
    return board;
}

const PROMOTION_PIECES_WHITE = [
    { symbol: "♕", piece: "q", label: "Queen" },
    { symbol: "♖", piece: "r", label: "Rook" },
    { symbol: "♗", piece: "b", label: "Bishop" },
    { symbol: "♘", piece: "n", label: "Knight" },
];
const PROMOTION_PIECES_BLACK = [
    { symbol: "♛", piece: "q", label: "Queen" },
    { symbol: "♜", piece: "r", label: "Rook" },
    { symbol: "♝", piece: "b", label: "Bishop" },
    { symbol: "♞", piece: "n", label: "Knight" },
];

const ChessBoard: React.FC = () => {
    const { fen, makePlayerMove, isLoading, boardFlipped, gameStarted, isCheck, playerColor } = useChess();
    const board = fen ? parseFEN(fen) : Array(8).fill(null).map(() => Array(8).fill(""));
    const [selected, setSelected] = useState<{ row: number; col: number } | null>(null);
    const [dragging, setDragging] = useState<{ row: number; col: number } | null>(null);
    const [dragPos, setDragPos] = useState<{ x: number; y: number } | null>(null);
    const [pendingPromotion, setPendingPromotion] = useState<{ from: string; to: string; col: number; isWhite: boolean } | null>(null);
    const boardRef = useRef<HTMLDivElement>(null);

    const getSquareName = (row: number, col: number) => {
        const actualRow = boardFlipped ? 7 - row : row;
        const actualCol = boardFlipped ? 7 - col : col;
        const file = "abcdefgh"[actualCol];
        const rank = 8 - actualRow;
        return `${file}${rank}`;
    };

    const getBoardDisplay = () => {
        if (boardFlipped) {
            return board.map(row => [...row].reverse()).reverse();
        }
        return board;
    };

    const getCellColor = (rowIndex: number, colIndex: number) => {
        const actualRow = boardFlipped ? 7 - rowIndex : rowIndex;
        const actualCol = boardFlipped ? 7 - colIndex : colIndex;
        return (actualRow + actualCol) % 2 === 0 ? styles.light : styles.dark;
    };

    const getSquareFromPoint = useCallback((clientX: number, clientY: number): { row: number; col: number } | null => {
        if (!boardRef.current) return null;
        const rect = boardRef.current.getBoundingClientRect();
        const cellSize = rect.width / 8;
        const col = Math.floor((clientX - rect.left) / cellSize);
        const row = Math.floor((clientY - rect.top) / cellSize);
        if (row < 0 || row > 7 || col < 0 || col > 7) return null;
        return { row, col };
    }, []);

    const isKingInCheck = (piece: string): boolean => {
        if (!isCheck) return false;
        const fenTurn = fen?.split(" ")[1];
        const isWhiteTurn = fenTurn === "w";
        if (isWhiteTurn && piece === "K") return true;
        if (!isWhiteTurn && piece === "k") return true;
        return false;
    };

    // Check if a move is a pawn promotion
    const isPromotionMove = (fromSquare: string, toSquare: string): boolean => {
        const displayBoard = getBoardDisplay();
        // Find the piece at the from square
        const fromFile = fromSquare.charCodeAt(0) - 97; // a=0, b=1, ...
        const fromRank = parseInt(fromSquare[1]);       // 1-8
        const actualFromRow = 8 - fromRank;
        const actualFromCol = fromFile;
        const displayFromRow = boardFlipped ? 7 - actualFromRow : actualFromRow;
        const displayFromCol = boardFlipped ? 7 - actualFromCol : actualFromCol;

        const piece = displayBoard[displayFromRow]?.[displayFromCol];
        if (!piece) return false;

        const toRank = parseInt(toSquare[1]);
        const isPawn = piece === "P" || piece === "p";
        const isWhitePawn = piece === "P";

        return isPawn && ((isWhitePawn && toRank === 8) || (!isWhitePawn && toRank === 1));
    };

    const attemptMove = async (from: string, to: string, displayCol: number) => {
        if (isPromotionMove(from, to)) {
            const isWhite = playerColor === "white";
            setPendingPromotion({ from, to, col: displayCol, isWhite });
        } else {
            await makePlayerMove(from, to);
        }
    };

    const handlePromotionChoice = async (piece: string) => {
        if (!pendingPromotion) return;
        await makePlayerMove(pendingPromotion.from, pendingPromotion.to, piece);
        setPendingPromotion(null);
        setSelected(null);
    };

    const cancelPromotion = () => {
        setPendingPromotion(null);
        setSelected(null);
    };

    // ---- Click to move ----
    const handleClick = async (row: number, col: number) => {
        if (isLoading || !gameStarted || dragging || pendingPromotion) return;
        const displayBoard = getBoardDisplay();

        if (!selected) {
            if (displayBoard[row][col] !== "") setSelected({ row, col });
        } else {
            if (selected.row === row && selected.col === col) {
                setSelected(null);
                return;
            }
            const clickedPiece = displayBoard[row][col];
            const selectedPiece = displayBoard[selected.row][selected.col];
            const isSameColor = clickedPiece !== "" && selectedPiece !== "" &&
                (clickedPiece === clickedPiece.toUpperCase()) === (selectedPiece === selectedPiece.toUpperCase());
            if (isSameColor) {
                setSelected({ row, col });
                return;
            }
            const from = getSquareName(selected.row, selected.col);
            const to = getSquareName(row, col);
            await attemptMove(from, to, col);
            if (!isPromotionMove(from, to)) setSelected(null);
        }
    };

    // ---- Drag & drop ----
    const handlePointerDown = (e: React.PointerEvent, row: number, col: number) => {
        if (isLoading || !gameStarted || pendingPromotion) return;
        const displayBoard = getBoardDisplay();
        if (displayBoard[row][col] === "") return;

        setDragging({ row, col });
        setSelected({ row, col });
        setDragPos({ x: e.clientX, y: e.clientY });
        (e.target as HTMLElement).setPointerCapture(e.pointerId);
    };

    const handlePointerMove = (e: React.PointerEvent) => {
        if (!dragging) return;
        setDragPos({ x: e.clientX, y: e.clientY });
    };

    const handlePointerUp = async (e: React.PointerEvent) => {
        if (!dragging) return;

        const target = getSquareFromPoint(e.clientX, e.clientY);
        if (target && (target.row !== dragging.row || target.col !== dragging.col)) {
            const from = getSquareName(dragging.row, dragging.col);
            const to = getSquareName(target.row, target.col);
            await attemptMove(from, to, target.col);
            if (!isPromotionMove(from, to)) setSelected(null);
        }

        setDragging(null);
        setDragPos(null);
    };

    const displayBoard = getBoardDisplay();

    // Render the dragged piece floating under the cursor
    const renderDragPiece = () => {
        if (!dragging || !dragPos) return null;
        const piece = displayBoard[dragging.row][dragging.col];
        if (!piece) return null;
        const isWhitePiece = piece === piece.toUpperCase();
        return (
            <div
                className={styles.dragPiece}
                style={{
                    left: dragPos.x,
                    top: dragPos.y,
                    color: isWhitePiece ? "#fff" : "#000",
                    textShadow: isWhitePiece
                        ? "1px 1px 0 #000, -1px 1px 0 #000, 1px -1px 0 #000, -1px -1px 0 #000"
                        : "1px 1px 0 rgba(255,255,255,0.4)",
                }}
            >
                {pieceSymbols[piece]}
            </div>
        );
    };

    // Render promotion picker overlay on the board
    const renderPromotionPicker = () => {
        if (!pendingPromotion) return null;
        const pieces = pendingPromotion.isWhite ? PROMOTION_PIECES_WHITE : PROMOTION_PIECES_BLACK;
        // Show picker on top (white promoting) or bottom (black promoting) of the target column
        const promoteAtTop = pendingPromotion.isWhite ? !boardFlipped : boardFlipped;

        return (
            <>
                <div className={styles.promotionOverlay} onClick={cancelPromotion} />
                <div
                    className={styles.promotionPicker}
                    style={{
                        left: `${pendingPromotion.col * 12.5}%`,
                        [promoteAtTop ? "top" : "bottom"]: "0",
                    }}
                >
                    {pieces.map((p) => (
                        <div
                            key={p.piece}
                            className={styles.promotionOption}
                            onClick={() => handlePromotionChoice(p.piece)}
                            title={p.label}
                        >
                            <span style={{
                                color: pendingPromotion.isWhite ? "#fff" : "#000",
                                textShadow: pendingPromotion.isWhite
                                    ? "1px 1px 0 #000, -1px 1px 0 #000, 1px -1px 0 #000, -1px -1px 0 #000"
                                    : "1px 1px 0 rgba(255,255,255,0.3)",
                            }}>
                                {p.symbol}
                            </span>
                        </div>
                    ))}
                </div>
            </>
        );
    };

    return (
        <>
            <div
                className={styles.board}
                ref={boardRef}
                onPointerMove={handlePointerMove}
                onPointerUp={handlePointerUp}
            >
                {displayBoard.map((row, rowIndex) => (
                    <div className={styles.row} key={rowIndex}>
                        {row.map((cell, colIndex) => {
                            const square = getSquareName(rowIndex, colIndex);
                            const isSelected = selected?.row === rowIndex && selected?.col === colIndex;
                            const isDragSource = dragging?.row === rowIndex && dragging?.col === colIndex;
                            const isWhitePiece = cell === cell.toUpperCase() && cell !== "";
                            const kingCheck = cell !== "" && isKingInCheck(cell);

                            return (
                                <div
                                    key={square}
                                    className={`${styles.cell} ${getCellColor(rowIndex, colIndex)} ${isSelected ? styles.selected : ""} ${kingCheck ? styles.inCheck : ""}`}
                                    onClick={() => handleClick(rowIndex, colIndex)}
                                    onPointerDown={(e) => handlePointerDown(e, rowIndex, colIndex)}
                                >
                                    <span
                                        className={`${styles.piece} ${isDragSource ? styles.dragSource : ""}`}
                                        style={{
                                            color: isWhitePiece ? "#fff" : "#000",
                                            textShadow: isWhitePiece
                                                ? "1px 1px 0 #000, -1px 1px 0 #000, 1px -1px 0 #000, -1px -1px 0 #000"
                                                : "none",
                                        }}
                                    >
                                        {pieceSymbols[cell] || ""}
                                    </span>

                                    {rowIndex === 7 && (
                                        <span className={styles.fileLabel}>
                                            {boardFlipped ? "hgfedcba"[colIndex] : "abcdefgh"[colIndex]}
                                        </span>
                                    )}
                                    {colIndex === 0 && (
                                        <span className={styles.rankLabel}>
                                            {boardFlipped ? rowIndex + 1 : 8 - rowIndex}
                                        </span>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                ))}

                {/* Promotion picker on the board */}
                {renderPromotionPicker()}
            </div>
            {renderDragPiece()}
        </>
    );
};

export default ChessBoard;

