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
        return petRepository.findAll();
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
