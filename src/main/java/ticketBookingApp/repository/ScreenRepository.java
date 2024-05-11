package ticketBookingApp.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import ticketBookingApp.entity.Screen;

public interface ScreenRepository extends JpaRepository<Screen, Long> {
}