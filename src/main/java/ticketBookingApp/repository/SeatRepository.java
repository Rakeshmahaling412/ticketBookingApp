package ticketBookingApp.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import ticketBookingApp.entity.Seat;

import java.util.List;

public interface SeatRepository extends JpaRepository<Seat, Long> {
    List<Seat> findByScreenId(Long screenId);
    @Query("SELECT s FROM Seat s WHERE s.screen.id = :screenId AND s.isBooked = false")
    List<Seat> findVacantSeats(Long screenId);

}
