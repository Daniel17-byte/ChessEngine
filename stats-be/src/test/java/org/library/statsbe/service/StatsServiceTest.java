package org.library.statsbe.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.library.statsbe.model.GameStat;
import org.library.statsbe.repository.StatsRepository;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Arrays;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class StatsServiceTest {

    @Mock
    private StatsRepository repository;

    private StatsService service;

    @BeforeEach
    void setUp() {
        service = new StatsService(repository);
    }

    // ─── Update Win ─────────────────────────────────────────────────────

    @Test
    @DisplayName("updateWin → new user → creates stat with 1 win")
    void updateWin_newUser_createsStatWith1Win() {
        when(repository.findByUserId("user1")).thenReturn(Optional.empty());
        when(repository.save(any(GameStat.class))).thenAnswer(i -> i.getArgument(0));

        GameStat result = service.updateWin("user1");

        assertEquals(1, result.getWins());
        assertEquals(0, result.getLosses());
        assertEquals(0, result.getDraws());
        assertEquals("user1", result.getUserId());
    }

    @Test
    @DisplayName("updateWin → existing user → increments wins by 1")
    void updateWin_existingUser_incrementsWins() {
        GameStat existing = new GameStat(1L, "user1", 5, 3, 2);
        when(repository.findByUserId("user1")).thenReturn(Optional.of(existing));
        when(repository.save(any(GameStat.class))).thenAnswer(i -> i.getArgument(0));

        GameStat result = service.updateWin("user1");

        assertEquals(6, result.getWins());
        assertEquals(3, result.getLosses());
        assertEquals(2, result.getDraws());
    }

    @Test
    @DisplayName("updateWin → saves to repository")
    void updateWin_savesToRepository() {
        when(repository.findByUserId("user1")).thenReturn(Optional.empty());
        when(repository.save(any(GameStat.class))).thenAnswer(i -> i.getArgument(0));

        service.updateWin("user1");

        verify(repository).save(any(GameStat.class));
    }

    // ─── Update Loss ────────────────────────────────────────────────────

    @Test
    @DisplayName("updateLoss → new user → creates stat with 1 loss")
    void updateLoss_newUser_createsStatWith1Loss() {
        when(repository.findByUserId("user1")).thenReturn(Optional.empty());
        when(repository.save(any(GameStat.class))).thenAnswer(i -> i.getArgument(0));

        GameStat result = service.updateLoss("user1");

        assertEquals(0, result.getWins());
        assertEquals(1, result.getLosses());
        assertEquals(0, result.getDraws());
    }

    @Test
    @DisplayName("updateLoss → existing user → increments losses by 1")
    void updateLoss_existingUser_incrementsLosses() {
        GameStat existing = new GameStat(1L, "user1", 5, 3, 2);
        when(repository.findByUserId("user1")).thenReturn(Optional.of(existing));
        when(repository.save(any(GameStat.class))).thenAnswer(i -> i.getArgument(0));

        GameStat result = service.updateLoss("user1");

        assertEquals(5, result.getWins());
        assertEquals(4, result.getLosses());
        assertEquals(2, result.getDraws());
    }

    // ─── Update Draw ────────────────────────────────────────────────────

    @Test
    @DisplayName("updateDraw → new user → creates stat with 1 draw")
    void updateDraw_newUser_createsStatWith1Draw() {
        when(repository.findByUserId("user1")).thenReturn(Optional.empty());
        when(repository.save(any(GameStat.class))).thenAnswer(i -> i.getArgument(0));

        GameStat result = service.updateDraw("user1");

        assertEquals(0, result.getWins());
        assertEquals(0, result.getLosses());
        assertEquals(1, result.getDraws());
    }

    @Test
    @DisplayName("updateDraw → existing user → increments draws by 1")
    void updateDraw_existingUser_incrementsDraws() {
        GameStat existing = new GameStat(1L, "user1", 5, 3, 2);
        when(repository.findByUserId("user1")).thenReturn(Optional.of(existing));
        when(repository.save(any(GameStat.class))).thenAnswer(i -> i.getArgument(0));

        GameStat result = service.updateDraw("user1");

        assertEquals(5, result.getWins());
        assertEquals(3, result.getLosses());
        assertEquals(3, result.getDraws());
    }

    // ─── Get All Stats ──────────────────────────────────────────────────

    @Test
    @DisplayName("getAllStats → returns all stats from repository")
    void getAllStats_returnsAll() {
        GameStat s1 = new GameStat(1L, "user1", 10, 5, 2);
        GameStat s2 = new GameStat(2L, "user2", 3, 7, 1);

        when(repository.findAll()).thenReturn(Arrays.asList(s1, s2));

        List<GameStat> result = service.getAllStats();

        assertEquals(2, result.size());
        verify(repository).findAll();
    }

    @Test
    @DisplayName("getAllStats → empty → returns empty list")
    void getAllStats_empty_returnsEmptyList() {
        when(repository.findAll()).thenReturn(List.of());

        List<GameStat> result = service.getAllStats();

        assertTrue(result.isEmpty());
    }

    // ─── Get By User ID ─────────────────────────────────────────────────

    @Test
    @DisplayName("getByUserId → existing → returns stat")
    void getByUserId_existing_returnsStat() {
        GameStat stat = new GameStat(1L, "user1", 10, 5, 2);
        when(repository.findByUserId("user1")).thenReturn(Optional.of(stat));

        GameStat result = service.getByUserId("user1");

        assertNotNull(result);
        assertEquals("user1", result.getUserId());
        assertEquals(10, result.getWins());
    }

    @Test
    @DisplayName("getByUserId → non-existing → returns null")
    void getByUserId_nonExisting_returnsNull() {
        when(repository.findByUserId("unknown")).thenReturn(Optional.empty());

        GameStat result = service.getByUserId("unknown");

        assertNull(result);
    }

    // ─── Multiple Updates ───────────────────────────────────────────────

    @Test
    @DisplayName("Multiple updates → stats accumulate correctly")
    void multipleUpdates_statsAccumulate() {
        // Simulate: win, win, loss, draw
        GameStat stat = new GameStat(1L, "user1", 0, 0, 0);

        when(repository.findByUserId("user1")).thenReturn(Optional.of(stat));
        when(repository.save(any(GameStat.class))).thenAnswer(i -> i.getArgument(0));

        service.updateWin("user1");   // wins=1
        service.updateWin("user1");   // wins=2
        service.updateLoss("user1");  // losses=1
        service.updateDraw("user1");  // draws=1

        assertEquals(2, stat.getWins());
        assertEquals(1, stat.getLosses());
        assertEquals(1, stat.getDraws());
    }
}

