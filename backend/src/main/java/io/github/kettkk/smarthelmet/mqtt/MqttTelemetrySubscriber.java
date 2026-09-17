package io.github.kettkk.smarthelmet.mqtt;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.github.kettkk.smarthelmet.telemetry.TelemetryIngestionService;
import io.github.kettkk.smarthelmet.telemetry.TelemetryMessage;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validator;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallbackExtended;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

@Component
@ConditionalOnProperty(name = "app.mqtt.enabled", havingValue = "true", matchIfMissing = true)
public class MqttTelemetrySubscriber implements MqttCallbackExtended {
    private static final Logger log = LoggerFactory.getLogger(MqttTelemetrySubscriber.class);

    private final ObjectMapper objectMapper;
    private final Validator validator;
    private final TelemetryIngestionService ingestionService;
    private final String brokerUri;
    private final String topic;
    private final String clientId;
    private final ScheduledExecutorService reconnectExecutor = Executors.newSingleThreadScheduledExecutor(r -> {
        Thread thread = new Thread(r, "mqtt-reconnect");
        thread.setDaemon(true);
        return thread;
    });

    private MqttClient client;

    public MqttTelemetrySubscriber(
            ObjectMapper objectMapper,
            Validator validator,
            TelemetryIngestionService ingestionService,
            @Value("${app.mqtt.broker-uri}") String brokerUri,
            @Value("${app.mqtt.topic}") String topic,
            @Value("${app.mqtt.client-id}") String clientId) {
        this.objectMapper = objectMapper;
        this.validator = validator;
        this.ingestionService = ingestionService;
        this.brokerUri = brokerUri;
        this.topic = topic;
        this.clientId = clientId;
    }

    @PostConstruct
    void start() throws Exception {
        client = new MqttClient(brokerUri, clientId, new MemoryPersistence());
        client.setCallback(this);
        reconnectExecutor.scheduleWithFixedDelay(this::ensureConnected, 0, 5, TimeUnit.SECONDS);
    }

    private void ensureConnected() {
        if (client == null || client.isConnected()) {
            return;
        }
        try {
            MqttConnectOptions options = new MqttConnectOptions();
            options.setAutomaticReconnect(true);
            options.setCleanSession(true);
            options.setConnectionTimeout(5);
            client.connect(options);
        } catch (Exception exception) {
            log.warn("MQTT broker unavailable at {}; retrying", brokerUri);
        }
    }

    @Override
    public void connectComplete(boolean reconnect, String serverURI) {
        try {
            client.subscribe(topic, 1);
            log.info("Subscribed to MQTT topic {} at {}", topic, serverURI);
        } catch (Exception exception) {
            log.error("Failed to subscribe to MQTT topic {}", topic, exception);
        }
    }

    @Override
    public void connectionLost(Throwable cause) {
        log.warn("MQTT connection lost; automatic reconnect is enabled", cause);
    }

    @Override
    public void messageArrived(String receivedTopic, MqttMessage mqttMessage) {
        try {
            String payload = new String(mqttMessage.getPayload(), StandardCharsets.UTF_8);
            TelemetryMessage message = objectMapper.readValue(payload, TelemetryMessage.class);
            Set<ConstraintViolation<TelemetryMessage>> violations = validator.validate(message);
            if (!violations.isEmpty()) {
                log.warn("Rejected invalid telemetry on {}: {}", receivedTopic, violations);
                return;
            }
            ingestionService.ingest(message);
            log.debug("Stored telemetry from {}", message.deviceId());
        } catch (Exception exception) {
            log.warn("Rejected unreadable telemetry on {}: {}", receivedTopic, exception.getMessage());
        }
    }

    @Override
    public void deliveryComplete(IMqttDeliveryToken token) {
        // Subscriber only.
    }

    @PreDestroy
    void stop() {
        reconnectExecutor.shutdownNow();
        if (client != null) {
            try {
                if (client.isConnected()) {
                    client.disconnect();
                }
                client.close();
            } catch (Exception exception) {
                log.debug("MQTT shutdown completed with an ignored error", exception);
            }
        }
    }
}
