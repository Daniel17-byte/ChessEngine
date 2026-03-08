package org.library.statsbe.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;

@Entity
public class GameStat {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String userId;
    private int wins;
    private int losses;
    private int draws;

    public GameStat(Long id, String userId, int wins, int losses, int draws) {
        this.id = id;
        this.userId = userId;
        this.wins = wins;
        this.losses = losses;
        this.draws = draws;
    }

    public GameStat() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }

    public int getWins() { return wins; }
    public void setWins(int wins) { this.wins = wins; }

    public int getLosses() { return losses; }
    public void setLosses(int losses) { this.losses = losses; }

    public int getDraws() { return draws; }
    public void setDraws(int draws) { this.draws = draws; }

    @JsonProperty("totalGames")
    public int getTotalGames() {
        return wins + losses + draws;
    }

    @JsonProperty("winRate")
    public double getWinRate() {
        int total = getTotalGames();
        if (total == 0) return 0.0;
        return (double) wins / total;
    }
}