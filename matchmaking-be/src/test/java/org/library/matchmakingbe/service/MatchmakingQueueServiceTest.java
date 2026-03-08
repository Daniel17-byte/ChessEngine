package org.library.matchmakingbe.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.library.matchmakingbe.dto.QueueStatusResponse;
import org.library.matchmakingbe.model.Match;
import org.library.matchmakingbe.repository.MatchRepository;
import org.library.matchmakingbe.util.MatchStatus;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.amqp.rabbit.core.RabbitTemplate;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class MatchmakingQueueServiceTest {

    @Mock
    private RabbitTemplate rabbitTemplate;

    @Mock
    private MatchRepository matchRepository;

    private MatchmakingQueueService service;

    @BeforeEach
    void setUp() {
        service = new MatchmakingQueueService(rabbitTemplate, matchRepository);
    }

    // ─── Join Queue ─────────────────────────────────────────────────────

    @Test
    @DisplayName("Player joins empty queue → status is QUEUED, position 1")
    void joinQueue_emptyQueue_playerIsQueued() {
        QueueStatusResponse response = service.joinQueue("p1", "Alice", 1200);

        assertEquals("QUEUED", response.getStatus());
        assertEquals("p1", response.getPlayerId());
        assertEquals(1, response.getQueuePosition());
        assertEquals(1, response.getQueueSize());
        assertNull(response.getMatchId());
    }

    @Test
    @DisplayName("Player joins queue → message published to RabbitMQ")
    void joinQueue_publishesToRabbitMQ() {
        service.joinQueue("p1", "Alice", 1200);

        verify(rabbitTemplate, atLeastOnce()).convertAndSend(anyString(), anyString(), any(Object.class));
    }

    @Test
    @DisplayName("Two players join → they are matched immediately")
    void joinQueue_twoPlayers_matchedImmediately() {
        // Stub matchRepository.save to return a match with an ID
        when(matchRepository.save(any(Match.class))).thenAnswer(invocation -> {
            Match m = invocation.getArgument(0);
            m.setId(100L);
            return m;
        });

        QueueStatusResponse r1 = service.joinQueue("p1", "Alice", 1200);
        QueueStatusResponse r2 = service.joinQueue("p2", "Bob", 1300);

        // After second player joins, both should be matched
        // r1 was QUEUED when first returned, but now let's check current status
        QueueStatusResponse s1 = service.getQueueStatus("p1");
        QueueStatusResponse s2 = service.getQueueStatus("p2");

        assertEquals("MATCHED", s1.getStatus());
        assertEquals("MATCHED", s2.getStatus());
        assertEquals(100L, s1.getMatchId());
        assertEquals(100L, s2.getMatchId());
    }

    @Test
    @DisplayName("Two players matched → Match saved in DB with ONGOING status")
    void joinQueue_twoPlayers_matchSavedInDB() {
        when(matchRepository.save(any(Match.class))).thenAnswer(invocation -> {
            Match m = invocation.getArgument(0);
            m.setId(1L);
            return m;
        });

        service.joinQueue("p1", "Alice", 1200);
        service.joinQueue("p2", "Bob", 1300);

        ArgumentCaptor<Match> captor = ArgumentCaptor.forClass(Match.class);
        verify(matchRepository).save(captor.capture());

        Match saved = captor.getValue();
        assertEquals("p1", saved.getPlayerOneId());
        assertEquals("p2", saved.getPlayerTwoId());
        assertEquals(MatchStatus.ONGOING, saved.getStatus());
    }

    @Test
    @DisplayName("Two players matched → match-found event published to RabbitMQ")
    void joinQueue_twoPlayers_matchFoundEventPublished() {
        when(matchRepository.save(any(Match.class))).thenAnswer(invocation -> {
            Match m = invocation.getArgument(0);
            m.setId(1L);
            return m;
        });

        service.joinQueue("p1", "Alice", 1200);
        service.joinQueue("p2", "Bob", 1300);

        // 2 join messages + 1 match-found event = at least 3 calls
        verify(rabbitTemplate, atLeast(3)).convertAndSend(anyString(), anyString(), any(Object.class));
    }

    @Test
    @DisplayName("Two players matched → queue is empty")
    void joinQueue_twoPlayers_queueEmpty() {
        when(matchRepository.save(any(Match.class))).thenAnswer(invocation -> {
            Match m = invocation.getArgument(0);
            m.setId(1L);
            return m;
        });

        service.joinQueue("p1", "Alice", 1200);
        service.joinQueue("p2", "Bob", 1300);

        assertEquals(0, service.getQueueSize());
    }

    @Test
    @DisplayName("Same player joins twice → returns existing status, no duplicate")
    void joinQueue_duplicateJoin_noDuplicate() {
        service.joinQueue("p1", "Alice", 1200);
        QueueStatusResponse r2 = service.joinQueue("p1", "Alice", 1200);

        assertEquals("QUEUED", r2.getStatus());
        assertEquals(1, service.getQueueSize());
    }

    @Test
    @DisplayName("Already matched player tries to join → returns MATCHED status")
    void joinQueue_alreadyMatched_returnsMatchedStatus() {
        when(matchRepository.save(any(Match.class))).thenAnswer(invocation -> {
            Match m = invocation.getArgument(0);
            m.setId(42L);
            return m;
        });

        service.joinQueue("p1", "Alice", 1200);
        service.joinQueue("p2", "Bob", 1300);

        // p1 is now matched, try to join again
        QueueStatusResponse response = service.joinQueue("p1", "Alice", 1200);
        assertEquals("MATCHED", response.getStatus());
        assertEquals(42L, response.getMatchId());
    }

    // ─── Leave Queue ────────────────────────────────────────────────────

    @Test
    @DisplayName("Player leaves queue → status is NOT_IN_QUEUE")
    void leaveQueue_playerInQueue_removedSuccessfully() {
        service.joinQueue("p1", "Alice", 1200);
        QueueStatusResponse response = service.leaveQueue("p1");

        assertEquals("NOT_IN_QUEUE", response.getStatus());
        assertEquals(0, service.getQueueSize());
    }

    @Test
    @DisplayName("Player not in queue leaves → returns NOT_IN_QUEUE")
    void leaveQueue_playerNotInQueue_returnsNotInQueue() {
        QueueStatusResponse response = service.leaveQueue("unknown");

        assertEquals("NOT_IN_QUEUE", response.getStatus());
    }

    @Test
    @DisplayName("Matched player leaves → clears matched status")
    void leaveQueue_matchedPlayer_clearsMatchedStatus() {
        when(matchRepository.save(any(Match.class))).thenAnswer(invocation -> {
            Match m = invocation.getArgument(0);
            m.setId(1L);
            return m;
        });

        service.joinQueue("p1", "Alice", 1200);
        service.joinQueue("p2", "Bob", 1300);

        // p1 is matched, now leaves
        QueueStatusResponse response = service.leaveQueue("p1");
        assertEquals("NOT_IN_QUEUE", response.getStatus());

        // Verify status is cleared
        QueueStatusResponse status = service.getQueueStatus("p1");
        assertEquals("NOT_IN_QUEUE", status.getStatus());
    }

    // ─── Get Queue Status ───────────────────────────────────────────────

    @Test
    @DisplayName("Unknown player → status is NOT_IN_QUEUE")
    void getQueueStatus_unknownPlayer_notInQueue() {
        QueueStatusResponse response = service.getQueueStatus("unknown");

        assertEquals("NOT_IN_QUEUE", response.getStatus());
        assertNull(response.getMatchId());
    }

    @Test
    @DisplayName("Queued players → correct positions in queue")
    void getQueueStatus_queuedPlayer_correctPosition() {
        // Only add one player (no match triggered, no need for mock)
        service.joinQueue("p1", "Alice", 1200);

        QueueStatusResponse r1 = service.getQueueStatus("p1");
        assertEquals("QUEUED", r1.getStatus());
        assertEquals(1, r1.getQueuePosition());
    }

    @Test
    @DisplayName("Single player in queue → position is 1, size is 1")
    void getQueueStatus_singlePlayer_position1() {
        service.joinQueue("p1", "Alice", 1200);
        QueueStatusResponse response = service.getQueueStatus("p1");

        assertEquals("QUEUED", response.getStatus());
        assertEquals(1, response.getQueuePosition());
        assertEquals(1, response.getQueueSize());
    }

    // ─── Get Queue Size ─────────────────────────────────────────────────

    @Test
    @DisplayName("Empty queue → size is 0")
    void getQueueSize_empty_returnsZero() {
        assertEquals(0, service.getQueueSize());
    }

    @Test
    @DisplayName("One player in queue → size is 1")
    void getQueueSize_onePlayer_returnsOne() {
        service.joinQueue("p1", "Alice", 1200);
        assertEquals(1, service.getQueueSize());
    }

    // ─── Multiple Matches ───────────────────────────────────────────────

    @Test
    @DisplayName("Four players join → two matches created")
    void joinQueue_fourPlayers_twoMatchesCreated() {
        when(matchRepository.save(any(Match.class))).thenAnswer(invocation -> {
            Match m = invocation.getArgument(0);
            m.setId((long) (Math.random() * 10000));
            return m;
        });

        service.joinQueue("p1", "Alice", 1200);
        service.joinQueue("p2", "Bob", 1300);
        service.joinQueue("p3", "Charlie", 1100);
        service.joinQueue("p4", "Diana", 1400);

        // 2 matches should have been created
        verify(matchRepository, times(2)).save(any(Match.class));
        assertEquals(0, service.getQueueSize());

        // All 4 players should be matched
        assertEquals("MATCHED", service.getQueueStatus("p1").getStatus());
        assertEquals("MATCHED", service.getQueueStatus("p2").getStatus());
        assertEquals("MATCHED", service.getQueueStatus("p3").getStatus());
        assertEquals("MATCHED", service.getQueueStatus("p4").getStatus());
    }

    @Test
    @DisplayName("Three players join → one match, one still in queue")
    void joinQueue_threePlayers_oneMatchOneQueued() {
        when(matchRepository.save(any(Match.class))).thenAnswer(invocation -> {
            Match m = invocation.getArgument(0);
            m.setId(1L);
            return m;
        });

        service.joinQueue("p1", "Alice", 1200);
        service.joinQueue("p2", "Bob", 1300);
        service.joinQueue("p3", "Charlie", 1100);

        verify(matchRepository, times(1)).save(any(Match.class));
        assertEquals(1, service.getQueueSize());

        // p1 and p2 matched, p3 still queued
        assertEquals("MATCHED", service.getQueueStatus("p1").getStatus());
        assertEquals("MATCHED", service.getQueueStatus("p2").getStatus());
        assertEquals("QUEUED", service.getQueueStatus("p3").getStatus());
    }
}

