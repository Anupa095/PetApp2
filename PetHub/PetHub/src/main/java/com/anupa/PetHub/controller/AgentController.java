package com.anupa.PetHub.controller;

import com.anupa.PetHub.model.SymptomQuery;
import com.anupa.PetHub.repository.SymptomQueryRepository;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/agent")
@CrossOrigin
public class AgentController {

    private final SymptomQueryRepository symptomQueryRepository;
    private final RestTemplate restTemplate;

    @Value("${agent.orchestrator.url:http://localhost:8000/orchestrate/symptom}")
    private String orchestratorUrl;

    public AgentController(SymptomQueryRepository symptomQueryRepository) {
        this.symptomQueryRepository = symptomQueryRepository;
        this.restTemplate = new RestTemplate();
    }

    @PostMapping("/chat")
    public ResponseEntity<?> chat(@RequestBody Map<String, Object> payload) {
        String message = String.valueOf(payload.getOrDefault("message", "")).trim();
        String userEmail = String.valueOf(payload.getOrDefault("userEmail", "anonymous@pethub.local")).trim();
        String sessionId = String.valueOf(payload.getOrDefault("sessionId", UUID.randomUUID().toString())).trim();

        if (message.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of(
                    "success", false,
                    "message", "Symptom message is required"
            ));
        }

        SymptomQuery logEntry = new SymptomQuery();
        logEntry.setUserEmail(userEmail);
        logEntry.setMessage(message);

        try {
            Map<String, Object> orchestratorRequest = new LinkedHashMap<>();
            orchestratorRequest.put("message", message);
            orchestratorRequest.put("user_email", userEmail);
            orchestratorRequest.put("session_id", sessionId);

            @SuppressWarnings("unchecked")
            Map<String, Object> orchestratorResponse =
                    restTemplate.postForObject(orchestratorUrl, orchestratorRequest, Map.class);

            logEntry.setStatus("SUCCESS");
            logEntry.setResponseText(safeTruncate(orchestratorResponse == null ? "" : orchestratorResponse.toString(), 3900));
            symptomQueryRepository.save(logEntry);

                Map<String, Object> response = new LinkedHashMap<>();
                response.put("success", true);
                response.put("sessionId", sessionId);
                response.put("data", orchestratorResponse == null ? Map.of() : orchestratorResponse);
                return ResponseEntity.ok(response);
        } catch (RestClientException ex) {
            logEntry.setStatus("FAILED");
            logEntry.setResponseText(safeTruncate(ex.getMessage(), 3900));
            symptomQueryRepository.save(logEntry);

            return ResponseEntity.status(503).body(Map.of(
                    "success", false,
                    "message", "AI orchestrator service is unavailable",
                    "details", ex.getMessage()
            ));
        }
    }

    @GetMapping("/admin/queries")
    public List<SymptomQuery> recentQueries() {
        return symptomQueryRepository.findTop50ByOrderByCreatedAtDesc();
    }

    private String safeTruncate(String text, int maxSize) {
        if (text == null) {
            return "";
        }
        return text.length() <= maxSize ? text : text.substring(0, maxSize);
    }
}
