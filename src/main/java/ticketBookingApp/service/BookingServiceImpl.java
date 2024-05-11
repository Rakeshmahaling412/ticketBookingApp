package ticketBookingApp.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import ticketBookingApp.entity.Booking;
import ticketBookingApp.entity.Screen;
import ticketBookingApp.entity.Seat;
import ticketBookingApp.entity.User;
import ticketBookingApp.repository.BookingRepository;
import ticketBookingApp.repository.ScreenRepository;
import ticketBookingApp.repository.SeatRepository;
import ticketBookingApp.repository.UserRepository;

import java.util.List;

@Service
public class BookingServiceImpl implements BookingService {

    @Autowired
    private BookingRepository bookingRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private ScreenRepository screenRepository;

    @Autowired
    private SeatRepository seatRepository;

    @Override
    public User getUserByUsername(String username) {
        return userRepository.findByUsername(username);
    }

    @Override
    public void bookSeats(Long screenId, int numberOfSeats, User user) {
        Screen screen = screenRepository.findById(screenId).orElse(null);
        if (screen == null) {
            return;
        }

        List<Seat> vacantSeats = seatRepository.findVacantSeats(screenId);
        if (vacantSeats.size() < numberOfSeats) {
            return;
        }

        for (int i = 0; i < numberOfSeats; i++) {
            Seat vacantSeat = vacantSeats.get(i);
            vacantSeat.setBooked(true);
            seatRepository.save(vacantSeat);

            Booking booking = new Booking();
            booking.setUser(user);
            booking.setSeat(vacantSeat);
            bookingRepository.save(booking);
        }
    }
}
