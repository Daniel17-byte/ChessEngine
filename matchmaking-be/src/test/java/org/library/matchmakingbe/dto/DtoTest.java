package org.library.matchmakingbe.dto;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class DtoTest {

    @Test
    @DisplayName("QueueEntry → constructor sets fields correctly")
    void queueEntry_constructorWorks() {
        QueueEntry entry = new QueueEntry("p1", "Alice", 1500);

        assertEquals("p1", entry.getPlayerId());
        assertEquals("Alice", entry.getPlayerName());
        assertEquals(1500, entry.getRating());
        assertNotNull(entry.getJoinedAt());
    }

    @Test
    @DisplayName("QueueEntry → setters work")
    void queueEntry_settersWork() {
        QueueEntry entry = new QueueEntry();
        entry.setPlayerId("p2");
        entry.setPlayerName("Bob");
        entry.setRating(1200);

        assertEquals("p2", entry.getPlayerId());
        assertEquals("Bob", entry.getPlayerName());
        assertEquals(1200, entry.getRating());
    }

    @Test
    @DisplayName("MatchFoundEvent → constructor sets all fields")
    void matchFoundEvent_constructorWorks() {
        MatchFoundEvent event = new MatchFoundEvent(1L, "p1", "Alice", "p2", "Bob");

        assertEquals(1L, event.getMatchId());
        assertEquals("p1", event.getPlayerOneId());
        assertEquals("Alice", event.getPlayerOneName());
        assertEquals("p2", event.getPlayerTwoId());
        assertEquals("Bob", event.getPlayerTwoName());
        assertNotNull(event.getMatchedAt());
    }

    @Test
    @DisplayName("QueueStatusResponse → constructor sets all fields")
    void queueStatusResponse_constructorWorks() {
        QueueStatusResponse response = new QueueStatusResponse("p1", "QUEUED", 3, 10, null);

        assertEquals("p1", response.getPlayerId());
        assertEquals("QUEUED", response.getStatus());
        assertEquals(3, response.getQueuePosition());
        assertEquals(10, response.getQueueSize());
        assertNull(response.getMatchId());
    }

    @Test
    @DisplayName("QueueStatusResponse → MATCHED with matchId")
    void queueStatusResponse_matched_hasMatchId() {
        QueueStatusResponse response = new QueueStatusResponse("p1", "MATCHED", 0, 0, 42L);

        assertEquals("MATCHED", response.getStatus());
        assertEquals(42L, response.getMatchId());
    }
}

