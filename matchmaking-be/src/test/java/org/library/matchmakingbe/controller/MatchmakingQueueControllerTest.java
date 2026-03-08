package org.library.matchmakingbe.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.library.matchmakingbe.dto.QueueStatusResponse;
import org.library.matchmakingbe.service.MatchmakingQueueService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Map;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(MatchmakingQueueController.class)
class MatchmakingQueueControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private MatchmakingQueueService queueService;

    private final ObjectMapper mapper = new ObjectMapper();

    // ─── POST /api/matchmaking/join ─────────────────────────────────────

    @Test
    @DisplayName("POST /join → 200 OK with QUEUED status")
    void joinQueue_validRequest_returnsQueued() throws Exception {
        when(queueService.joinQueue("p1", "Alice", 1200))
                .thenReturn(new QueueStatusResponse("p1", "QUEUED", 1, 1, null));

        mockMvc.perform(post("/api/matchmaking/join")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of(
                                "playerId", "p1",
                                "playerName", "Alice",
                                "rating", 1200
                        ))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("QUEUED"))
                .andExpect(jsonPath("$.playerId").value("p1"))
                .andExpect(jsonPath("$.queuePosition").value(1))
                .andExpect(jsonPath("$.queueSize").value(1));
    }

    @Test
    @DisplayName("POST /join → 200 OK with MATCHED status when instant match")
    void joinQueue_instantMatch_returnsMatched() throws Exception {
        when(queueService.joinQueue("p2", "Bob", 1300))
                .thenReturn(new QueueStatusResponse("p2", "MATCHED", 0, 0, 42L));

        mockMvc.perform(post("/api/matchmaking/join")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of(
                                "playerId", "p2",
                                "playerName", "Bob",
                                "rating", 1300
                        ))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("MATCHED"))
                .andExpect(jsonPath("$.matchId").value(42));
    }

    @Test
    @DisplayName("POST /join with missing playerId → 400 Bad Request")
    void joinQueue_missingPlayerId_returnsBadRequest() throws Exception {
        mockMvc.perform(post("/api/matchmaking/join")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of(
                                "playerName", "Alice"
                        ))))
                .andExpect(status().isBadRequest());
    }

    @Test
    @DisplayName("POST /join with blank playerId → 400 Bad Request")
    void joinQueue_blankPlayerId_returnsBadRequest() throws Exception {
        mockMvc.perform(post("/api/matchmaking/join")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of(
                                "playerId", "",
                                "playerName", "Alice"
                        ))))
                .andExpect(status().isBadRequest());
    }

    // ─── POST /api/matchmaking/leave ────────────────────────────────────

    @Test
    @DisplayName("POST /leave → 200 OK with NOT_IN_QUEUE")
    void leaveQueue_validRequest_returnsNotInQueue() throws Exception {
        when(queueService.leaveQueue("p1"))
                .thenReturn(new QueueStatusResponse("p1", "NOT_IN_QUEUE", 0, 0, null));

        mockMvc.perform(post("/api/matchmaking/leave")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(mapper.writeValueAsString(Map.of("playerId", "p1"))))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("NOT_IN_QUEUE"));
    }

    @Test
    @DisplayName("POST /leave with missing playerId → 400 Bad Request")
    void leaveQueue_missingPlayerId_returnsBadRequest() throws Exception {
        mockMvc.perform(post("/api/matchmaking/leave")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{}"))
                .andExpect(status().isBadRequest());
    }

    // ─── GET /api/matchmaking/status/{playerId} ─────────────────────────

    @Test
    @DisplayName("GET /status/p1 → returns current status")
    void getStatus_existingPlayer_returnsStatus() throws Exception {
        when(queueService.getQueueStatus("p1"))
                .thenReturn(new QueueStatusResponse("p1", "QUEUED", 3, 5, null));

        mockMvc.perform(get("/api/matchmaking/status/p1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("QUEUED"))
                .andExpect(jsonPath("$.queuePosition").value(3))
                .andExpect(jsonPath("$.queueSize").value(5));
    }

    @Test
    @DisplayName("GET /status/unknown → returns NOT_IN_QUEUE")
    void getStatus_unknownPlayer_returnsNotInQueue() throws Exception {
        when(queueService.getQueueStatus("unknown"))
                .thenReturn(new QueueStatusResponse("unknown", "NOT_IN_QUEUE", 0, 0, null));

        mockMvc.perform(get("/api/matchmaking/status/unknown"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.status").value("NOT_IN_QUEUE"));
    }

    // ─── GET /api/matchmaking/queue-size ─────────────────────────────────

    @Test
    @DisplayName("GET /queue-size → returns current queue size")
    void getQueueSize_returnsSize() throws Exception {
        when(queueService.getQueueSize()).thenReturn(7);

        mockMvc.perform(get("/api/matchmaking/queue-size"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.size").value(7));
    }
}

