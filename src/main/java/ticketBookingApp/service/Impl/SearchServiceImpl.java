package ticketBookingApp.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import ticketBookingApp.entity.Screen;
import ticketBookingApp.entity.Seat;
import ticketBookingApp.repository.ScreenRepository;
import ticketBookingApp.repository.SeatRepository;

import java.util.List;

@Service
public class SearchServiceImpl implements ScreenService  {

    @Autowired
    private ScreenRepository screenRepository;

    @Autowired
    private SeatRepository seatRepository;

    @Override
    public List<Screen> searchByScreenId(Long screenId) {
        Screen screen = screenRepository.findById(screenId).orElse(null);
        if (screen == null) {
            // Handle screen not found scenario
            return null;
        }
        List<Seat> seats = seatRepository.findByScreenId(screenId);

        screen.setSeats(seats);
        return List.of(screen);
    }

    @Override
    public List<Screen> getAlScreens() {
        return screenRepository.findAll();
    }


}
