package ticketBookingApp.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import ticketBookingApp.entity.Booking;

public interface BookingRepository extends JpaRepository<Booking, Long> {
}