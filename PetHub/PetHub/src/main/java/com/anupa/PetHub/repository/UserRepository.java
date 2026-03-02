package com.anupa.PetHub.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import com.anupa.PetHub.model.User;

import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Long> {

    Optional<User> findByEmail(String email);
}