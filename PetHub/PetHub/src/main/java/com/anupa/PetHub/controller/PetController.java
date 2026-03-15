package com.anupa.PetHub.controller;

import com.anupa.PetHub.model.Pet;
import com.anupa.PetHub.repository.PetRepository;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.MediaType;
import java.io.File;
//import java.net.MalformedURLException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.web.client.RestTemplate;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

@RestController
@RequestMapping("/pets")
@CrossOrigin
public class PetController {

    private final PetRepository petRepository;

    public PetController(PetRepository petRepository) {
        this.petRepository = petRepository;
    }

    // Get all pets
    @GetMapping
    public List<Pet> getAllPets() {
        List<Pet> pets = petRepository.findAll();
        // Populate sample data if empty
        if (pets.isEmpty()) {
            petRepository.save(new Pet("Buddy", "Dog", "default.jpg"));
            petRepository.save(new Pet("Whiskers", "Cat", "default.jpg"));
            petRepository.save(new Pet("Polly", "Parrot", "default.jpg"));
            pets = petRepository.findAll();
        }
        return pets;
    }

    // Get pet by ID
    @GetMapping("/{id}")
    public ResponseEntity<?> getPetById(@PathVariable Long id) {
        Optional<Pet> pet = petRepository.findById(id);
        if (pet.isPresent()) {
            return ResponseEntity.ok(pet.get());
        } else {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body("Pet not found");
        }
    }

    // Upload pet with image
    @PostMapping("/upload")
    public ResponseEntity<?> uploadPet(
            @RequestParam("name") String name,
            @RequestParam("type") String type,
            @RequestParam("image") MultipartFile image) {
        try {
            // ----- Python AI Image Verification -----
            try {
                RestTemplate restTemplate = new RestTemplate();
                String pythonApiUrl = "http://localhost:8000/verify-pet-image";

                HttpHeaders headers = new HttpHeaders();
                headers.setContentType(MediaType.MULTIPART_FORM_DATA);

                MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
                body.add("file", image.getResource());

                HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);
                ResponseEntity<String> pythonResponse = restTemplate.postForEntity(pythonApiUrl, requestEntity, String.class);

                ObjectMapper mapper = new ObjectMapper();
                JsonNode root = mapper.readTree(pythonResponse.getBody());
                boolean isValid = root.path("is_valid").asBoolean();

                if (!isValid) {
                    return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                            .body("Invalid photo. Please upload a clear picture of a cat or dog.");
                }
            } catch (Exception e) {
                // If the python service is down, we can log it and fail the upload, 
                // or you could choose to let it pass. We will fail it for security:
                e.printStackTrace();
                return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                        .body("AI Verification Service is unavailable. Cannot upload pet.");
            }
            // ----- End AI Verification -----

            // Define absolute folder path (project root uploads folder)
            String uploadDir = new File("uploads").getAbsolutePath();
            File dir = new File(uploadDir);
            if (!dir.exists())
                dir.mkdirs(); // safety check

            // Generate unique file name
            String fileName = UUID.randomUUID() + "_" + image.getOriginalFilename();
            Path filePath = Paths.get(uploadDir, fileName);

            // Save file
            Files.copy(image.getInputStream(), filePath, StandardCopyOption.REPLACE_EXISTING);

            // Save record to DB
            Pet pet = new Pet();
            pet.setName(name);
            pet.setType(type);
            pet.setImagePath(filePath.toString());
            petRepository.save(pet);

            return ResponseEntity.ok(pet);
        } catch (Exception e) {
            e.printStackTrace(); // very important
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("Upload failed");
        }
    }

    // Serve image
    @GetMapping("/image/{id}")
    public ResponseEntity<Resource> serveImage(@PathVariable Long id) {
        try {
            Optional<Pet> pet = petRepository.findById(id);
            if (pet.isPresent() && pet.get().getImagePath() != null) {
                Path path = Paths.get(pet.get().getImagePath());
                Resource resource = new UrlResource(path.toUri());

                if (resource.exists() || resource.isReadable()) {
                    String contentType = Files.probeContentType(path);
                    if (contentType == null) {
                        contentType = "image/jpeg";
                    }

                    return ResponseEntity.ok()
                            .contentType(MediaType.parseMediaType(contentType))
                            .body(resource);
                }
            }
            return ResponseEntity.notFound().build();
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }
}
