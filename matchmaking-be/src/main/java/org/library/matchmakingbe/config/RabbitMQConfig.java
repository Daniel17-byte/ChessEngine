package org.library.matchmakingbe.config;

import org.springframework.amqp.core.*;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {

    public static final String QUEUE_NAME = "matchmaking.queue";
    public static final String EXCHANGE_NAME = "matchmaking.exchange";
    public static final String ROUTING_KEY = "matchmaking.join";

    public static final String MATCH_FOUND_QUEUE = "matchmaking.match-found";
    public static final String MATCH_FOUND_ROUTING_KEY = "matchmaking.matched";

    @Bean
    public Queue matchmakingQueue() {
        return QueueBuilder.durable(QUEUE_NAME).build();
    }

    @Bean
    public Queue matchFoundQueue() {
        return QueueBuilder.durable(MATCH_FOUND_QUEUE).build();
    }

    @Bean
    public DirectExchange matchmakingExchange() {
        return new DirectExchange(EXCHANGE_NAME);
    }

    @Bean
    public Binding matchmakingBinding(Queue matchmakingQueue, DirectExchange matchmakingExchange) {
        return BindingBuilder.bind(matchmakingQueue).to(matchmakingExchange).with(ROUTING_KEY);
    }

    @Bean
    public Binding matchFoundBinding(Queue matchFoundQueue, DirectExchange matchmakingExchange) {
        return BindingBuilder.bind(matchFoundQueue).to(matchmakingExchange).with(MATCH_FOUND_ROUTING_KEY);
    }

    @Bean
    public MessageConverter jsonMessageConverter() {
        return new Jackson2JsonMessageConverter();
    }

    @Bean
    public RabbitTemplate rabbitTemplate(ConnectionFactory connectionFactory, MessageConverter jsonMessageConverter) {
        RabbitTemplate template = new RabbitTemplate(connectionFactory);
        template.setMessageConverter(jsonMessageConverter);
        return template;
    }
}

