package com.anupa.PetHub.controller;

import com.anupa.PetHub.model.User;
import com.anupa.PetHub.repository.UserRepository;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/auth")
@CrossOrigin
public class AuthController {

    private final UserRepository userRepository;
    private final BCryptPasswordEncoder passwordEncoder;

    public AuthController(UserRepository userRepository,
            BCryptPasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    // REGISTER
    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody User user) {
        Map<String, Object> response = new HashMap<>();

        if (userRepository.findByEmail(user.getEmail()).isPresent()) {
            response.put("success", false);
            response.put("message", "Email already exists!");
            return ResponseEntity.badRequest().body(response);
        }

        user.setPassword(passwordEncoder.encode(user.getPassword()));
        User savedUser = userRepository.save(user);

        response.put("success", true);
        response.put("message", "User registered successfully!");
        response.put("user", Map.of(
            "id", savedUser.getId(),
            "name", savedUser.getName(),
            "email", savedUser.getEmail()
        ));

        return ResponseEntity.ok(response);
    }

    // LOGIN
    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody User user) {
        Map<String, Object> response = new HashMap<>();

        Optional<User> existingUser = userRepository.findByEmail(user.getEmail());

        if (existingUser.isEmpty()) {
            response.put("success", false);
            response.put("message", "User not found!");
            return ResponseEntity.badRequest().body(response);
        }

        if (!passwordEncoder.matches(user.getPassword(), existingUser.get().getPassword())) {
            response.put("success", false);
            response.put("message", "Invalid password!");
            return ResponseEntity.badRequest().body(response);
        }

        User loggedInUser = existingUser.get();
        response.put("success", true);
        response.put("message", "Login successful!");
        response.put("user", Map.of(
            "id", loggedInUser.getId(),
            "name", loggedInUser.getName(),
            "email", loggedInUser.getEmail()
        ));

        return ResponseEntity.ok(response);
    }
}