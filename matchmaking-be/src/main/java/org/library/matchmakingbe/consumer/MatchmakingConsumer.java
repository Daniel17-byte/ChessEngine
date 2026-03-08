package org.library.matchmakingbe.consumer;

import org.library.matchmakingbe.config.RabbitMQConfig;
import org.library.matchmakingbe.dto.MatchFoundEvent;
import org.library.matchmakingbe.dto.QueueEntry;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

@Component
public class MatchmakingConsumer {

    private static final Logger log = LoggerFactory.getLogger(MatchmakingConsumer.class);

    /**
     * Listens for players joining the matchmaking queue.
     * Logging only — actual matching is done in MatchmakingQueueService.tryMatch().
     */
    @RabbitListener(queues = RabbitMQConfig.QUEUE_NAME)
    public void onPlayerJoinQueue(QueueEntry entry) {
        log.info("📩 RabbitMQ received queue entry: player={} ({}), rating={}",
                entry.getPlayerName(), entry.getPlayerId(), entry.getRating());
    }

    /**
     * Listens for match-found events.
     * Can be used by other services to react when a match is created.
     */
    @RabbitListener(queues = RabbitMQConfig.MATCH_FOUND_QUEUE)
    public void onMatchFound(MatchFoundEvent event) {
        log.info("🎮 Match found! matchId={} → {} vs {}",
                event.getMatchId(), event.getPlayerOneName(), event.getPlayerTwoName());
    }
}

