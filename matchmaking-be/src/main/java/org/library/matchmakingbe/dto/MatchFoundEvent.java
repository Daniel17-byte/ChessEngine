package org.library.matchmakingbe.dto;

import java.io.Serializable;
import java.time.Instant;

public class MatchFoundEvent implements Serializable {

    private Long matchId;
    private String playerOneId;
    private String playerOneName;
    private String playerTwoId;
    private String playerTwoName;
    private Instant matchedAt;

    public MatchFoundEvent() {}

    public MatchFoundEvent(Long matchId, String playerOneId, String playerOneName,
                           String playerTwoId, String playerTwoName) {
        this.matchId = matchId;
        this.playerOneId = playerOneId;
        this.playerOneName = playerOneName;
        this.playerTwoId = playerTwoId;
        this.playerTwoName = playerTwoName;
        this.matchedAt = Instant.now();
    }

    public Long getMatchId() { return matchId; }
    public void setMatchId(Long matchId) { this.matchId = matchId; }

    public String getPlayerOneId() { return playerOneId; }
    public void setPlayerOneId(String playerOneId) { this.playerOneId = playerOneId; }

    public String getPlayerOneName() { return playerOneName; }
    public void setPlayerOneName(String playerOneName) { this.playerOneName = playerOneName; }

    public String getPlayerTwoId() { return playerTwoId; }
    public void setPlayerTwoId(String playerTwoId) { this.playerTwoId = playerTwoId; }

    public String getPlayerTwoName() { return playerTwoName; }
    public void setPlayerTwoName(String playerTwoName) { this.playerTwoName = playerTwoName; }

    public Instant getMatchedAt() { return matchedAt; }
    public void setMatchedAt(Instant matchedAt) { this.matchedAt = matchedAt; }
}

