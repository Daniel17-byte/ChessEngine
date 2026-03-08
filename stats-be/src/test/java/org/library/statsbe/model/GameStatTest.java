package org.library.statsbe.model;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class GameStatTest {

    @Test
    @DisplayName("Default constructor → creates empty stat")
    void defaultConstructor_createsEmptyStat() {
        GameStat stat = new GameStat();
        assertEquals(0, stat.getWins());
        assertEquals(0, stat.getLosses());
        assertEquals(0, stat.getDraws());
    }

    @Test
    @DisplayName("All-args constructor → sets all fields")
    void allArgsConstructor_setsAllFields() {
        GameStat stat = new GameStat(1L, "user1", 10, 5, 3);

        assertEquals(1L, stat.getId());
        assertEquals("user1", stat.getUserId());
        assertEquals(10, stat.getWins());
        assertEquals(5, stat.getLosses());
        assertEquals(3, stat.getDraws());
    }

    @Test
    @DisplayName("getTotalGames → returns sum of wins, losses, draws")
    void getTotalGames_returnsSum() {
        GameStat stat = new GameStat(1L, "user1", 10, 5, 3);
        assertEquals(18, stat.getTotalGames());
    }

    @Test
    @DisplayName("getTotalGames → all zeros → returns 0")
    void getTotalGames_allZeros_returnsZero() {
        GameStat stat = new GameStat(1L, "user1", 0, 0, 0);
        assertEquals(0, stat.getTotalGames());
    }

    @Test
    @DisplayName("getWinRate → calculates correctly")
    void getWinRate_calculatesCorrectly() {
        GameStat stat = new GameStat(1L, "user1", 7, 2, 1);
        // winRate = 7 / 10 = 0.7
        assertEquals(0.7, stat.getWinRate(), 0.001);
    }

    @Test
    @DisplayName("getWinRate → no games → returns 0.0")
    void getWinRate_noGames_returnsZero() {
        GameStat stat = new GameStat(1L, "user1", 0, 0, 0);
        assertEquals(0.0, stat.getWinRate(), 0.001);
    }

    @Test
    @DisplayName("getWinRate → all wins → returns 1.0")
    void getWinRate_allWins_returnsOne() {
        GameStat stat = new GameStat(1L, "user1", 10, 0, 0);
        assertEquals(1.0, stat.getWinRate(), 0.001);
    }

    @Test
    @DisplayName("getWinRate → no wins → returns 0.0")
    void getWinRate_noWins_returnsZero() {
        GameStat stat = new GameStat(1L, "user1", 0, 5, 3);
        assertEquals(0.0, stat.getWinRate(), 0.001);
    }

    @Test
    @DisplayName("Setters work correctly")
    void settersWork() {
        GameStat stat = new GameStat();
        stat.setId(42L);
        stat.setUserId("bob");
        stat.setWins(15);
        stat.setLosses(8);
        stat.setDraws(4);

        assertEquals(42L, stat.getId());
        assertEquals("bob", stat.getUserId());
        assertEquals(15, stat.getWins());
        assertEquals(8, stat.getLosses());
        assertEquals(4, stat.getDraws());
        assertEquals(27, stat.getTotalGames());
    }
}

