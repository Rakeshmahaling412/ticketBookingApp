package ticketBookingApp.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import ticketBookingApp.entity.User;

public interface UserRepository extends JpaRepository<User, Long> {
    User findByUsername(String username);
}