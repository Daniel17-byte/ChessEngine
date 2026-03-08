package org.library.matchmakingbe.dto;

import java.io.Serializable;

public class QueueStatusResponse implements Serializable {

    private String playerId;
    private String status; // "QUEUED", "MATCHED", "NOT_IN_QUEUE"
    private int queuePosition;
    private int queueSize;
    private Long matchId;

    public QueueStatusResponse() {}

    public QueueStatusResponse(String playerId, String status, int queuePosition, int queueSize, Long matchId) {
        this.playerId = playerId;
        this.status = status;
        this.queuePosition = queuePosition;
        this.queueSize = queueSize;
        this.matchId = matchId;
    }

    public String getPlayerId() { return playerId; }
    public void setPlayerId(String playerId) { this.playerId = playerId; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public int getQueuePosition() { return queuePosition; }
    public void setQueuePosition(int queuePosition) { this.queuePosition = queuePosition; }

    public int getQueueSize() { return queueSize; }
    public void setQueueSize(int queueSize) { this.queueSize = queueSize; }

    public Long getMatchId() { return matchId; }
    public void setMatchId(Long matchId) { this.matchId = matchId; }
}

