package org.library.statsbe.controller;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.library.statsbe.model.GameStat;
import org.library.statsbe.service.StatsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Arrays;
import java.util.List;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(StatsController.class)
class StatsControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private StatsService service;

    // ─── POST /api/stats/win/{userId} ───────────────────────────────────

    @Test
    @DisplayName("POST /win/user1 → 200 with updated stat")
    void addWin_returnsUpdatedStat() throws Exception {
        GameStat stat = new GameStat(1L, "user1", 1, 0, 0);
        when(service.updateWin("user1")).thenReturn(stat);

        mockMvc.perform(post("/api/stats/win/user1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.userId").value("user1"))
                .andExpect(jsonPath("$.wins").value(1))
                .andExpect(jsonPath("$.losses").value(0))
                .andExpect(jsonPath("$.draws").value(0))
                .andExpect(jsonPath("$.totalGames").value(1))
                .andExpect(jsonPath("$.winRate").value(1.0));
    }

    // ─── POST /api/stats/loss/{userId} ──────────────────────────────────

    @Test
    @DisplayName("POST /loss/user1 → 200 with updated stat")
    void addLoss_returnsUpdatedStat() throws Exception {
        GameStat stat = new GameStat(1L, "user1", 0, 1, 0);
        when(service.updateLoss("user1")).thenReturn(stat);

        mockMvc.perform(post("/api/stats/loss/user1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.losses").value(1))
                .andExpect(jsonPath("$.winRate").value(0.0));
    }

    // ─── POST /api/stats/draw/{userId} ──────────────────────────────────

    @Test
    @DisplayName("POST /draw/user1 → 200 with updated stat")
    void addDraw_returnsUpdatedStat() throws Exception {
        GameStat stat = new GameStat(1L, "user1", 0, 0, 1);
        when(service.updateDraw("user1")).thenReturn(stat);

        mockMvc.perform(post("/api/stats/draw/user1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.draws").value(1));
    }

    // ─── GET /api/stats/all ─────────────────────────────────────────────

    @Test
    @DisplayName("GET /all → returns list of all stats")
    void getAll_returnsList() throws Exception {
        List<GameStat> stats = Arrays.asList(
                new GameStat(1L, "user1", 10, 5, 2),
                new GameStat(2L, "user2", 3, 7, 1)
        );
        when(service.getAllStats()).thenReturn(stats);

        mockMvc.perform(get("/api/stats/all"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(2))
                .andExpect(jsonPath("$[0].userId").value("user1"))
                .andExpect(jsonPath("$[0].wins").value(10))
                .andExpect(jsonPath("$[1].userId").value("user2"));
    }

    @Test
    @DisplayName("GET /all → empty → returns empty list")
    void getAll_empty_returnsEmptyList() throws Exception {
        when(service.getAllStats()).thenReturn(List.of());

        mockMvc.perform(get("/api/stats/all"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(0));
    }

    // ─── GET /api/stats/{userId} ────────────────────────────────────────

    @Test
    @DisplayName("GET /user1 → returns user stat with computed fields")
    void getByUser_returnsStatWithComputedFields() throws Exception {
        GameStat stat = new GameStat(1L, "user1", 7, 2, 1);
        when(service.getByUserId("user1")).thenReturn(stat);

        mockMvc.perform(get("/api/stats/user1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.userId").value("user1"))
                .andExpect(jsonPath("$.wins").value(7))
                .andExpect(jsonPath("$.losses").value(2))
                .andExpect(jsonPath("$.draws").value(1))
                .andExpect(jsonPath("$.totalGames").value(10))
                .andExpect(jsonPath("$.winRate").value(0.7));
    }

    @Test
    @DisplayName("GET /unknown → returns null body (200)")
    void getByUser_unknown_returnsNull() throws Exception {
        when(service.getByUserId("unknown")).thenReturn(null);

        mockMvc.perform(get("/api/stats/unknown"))
                .andExpect(status().isOk());
    }
}

