package org.library.matchmakingbe.controller;

import org.library.matchmakingbe.dto.QueueStatusResponse;
import org.library.matchmakingbe.service.MatchmakingQueueService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/matchmaking")
public class MatchmakingQueueController {

    private final MatchmakingQueueService queueService;

    public MatchmakingQueueController(MatchmakingQueueService queueService) {
        this.queueService = queueService;
    }

    /**
     * POST /api/matchmaking/join
     * Body: { "playerId": "123", "playerName": "Daniel", "rating": 1200 }
     *
     * Player joins the matchmaking queue. If another player is waiting,
     * a match is created immediately.
     */
    @PostMapping("/join")
    public ResponseEntity<QueueStatusResponse> joinQueue(@RequestBody Map<String, Object> body) {
        String playerId = (String) body.get("playerId");
        String playerName = (String) body.getOrDefault("playerName", "Player");
        int rating = body.containsKey("rating") ? ((Number) body.get("rating")).intValue() : 1200;

        if (playerId == null || playerId.isBlank()) {
            return ResponseEntity.badRequest().build();
        }

        QueueStatusResponse response = queueService.joinQueue(playerId, playerName, rating);
        return ResponseEntity.ok(response);
    }

    /**
     * POST /api/matchmaking/leave
     * Body: { "playerId": "123" }
     *
     * Player leaves the matchmaking queue.
     */
    @PostMapping("/leave")
    public ResponseEntity<QueueStatusResponse> leaveQueue(@RequestBody Map<String, String> body) {
        String playerId = body.get("playerId");

        if (playerId == null || playerId.isBlank()) {
            return ResponseEntity.badRequest().build();
        }

        QueueStatusResponse response = queueService.leaveQueue(playerId);
        return ResponseEntity.ok(response);
    }

    /**
     * GET /api/matchmaking/status/{playerId}
     *
     * Get the current queue status for a player.
     * Returns: QUEUED, MATCHED (with matchId), or NOT_IN_QUEUE
     */
    @GetMapping("/status/{playerId}")
    public ResponseEntity<QueueStatusResponse> getStatus(@PathVariable String playerId) {
        QueueStatusResponse response = queueService.getQueueStatus(playerId);
        return ResponseEntity.ok(response);
    }

    /**
     * GET /api/matchmaking/queue-size
     *
     * Get the number of players currently waiting in queue.
     */
    @GetMapping("/queue-size")
    public ResponseEntity<Map<String, Integer>> getQueueSize() {
        return ResponseEntity.ok(Map.of("size", queueService.getQueueSize()));
    }
}

