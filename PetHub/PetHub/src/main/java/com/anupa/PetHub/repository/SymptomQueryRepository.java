package com.anupa.PetHub.repository;

import com.anupa.PetHub.model.SymptomQuery;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface SymptomQueryRepository extends JpaRepository<SymptomQuery, Long> {
    List<SymptomQuery> findTop50ByOrderByCreatedAtDesc();
}