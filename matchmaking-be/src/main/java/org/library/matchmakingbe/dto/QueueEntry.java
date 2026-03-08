package org.library.matchmakingbe.dto;

import java.io.Serializable;
import java.time.Instant;

public class QueueEntry implements Serializable {

    private String playerId;
    private String playerName;
    private int rating;
    private Instant joinedAt;

    public QueueEntry() {}

    public QueueEntry(String playerId, String playerName, int rating) {
        this.playerId = playerId;
        this.playerName = playerName;
        this.rating = rating;
        this.joinedAt = Instant.now();
    }

    public String getPlayerId() { return playerId; }
    public void setPlayerId(String playerId) { this.playerId = playerId; }

    public String getPlayerName() { return playerName; }
    public void setPlayerName(String playerName) { this.playerName = playerName; }

    public int getRating() { return rating; }
    public void setRating(int rating) { this.rating = rating; }

    public Instant getJoinedAt() { return joinedAt; }
    public void setJoinedAt(Instant joinedAt) { this.joinedAt = joinedAt; }
}

