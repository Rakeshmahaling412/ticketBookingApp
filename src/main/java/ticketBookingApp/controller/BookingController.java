package ticketBookingApp.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import ticketBookingApp.entity.Booking;
import ticketBookingApp.entity.Screen;
import ticketBookingApp.entity.Seat;
import ticketBookingApp.entity.User;
import ticketBookingApp.service.BookingService;
import ticketBookingApp.service.ScreenService;

import java.security.Principal;
import java.util.ArrayList;
import java.util.List;

@Controller
public class BookingController {

    @Autowired
    private ScreenService screenService;

    @Autowired
    private BookingService bookingService;

    @GetMapping("/")
    public String showBookingForm(Model model, Principal principal) {
        List<Screen> screens = screenService.getAlScreens();

        if (principal != null) {
            User user = bookingService.getUserByUsername(principal.getName());
            List<Seat> bookedSeats = new ArrayList<>();
            for (Booking booking : user.getBookings()) {
                bookedSeats.add(booking.getSeat());
            }
            model.addAttribute("bookedSeats", bookedSeats);
        }

        model.addAttribute("screens", screens);
        return "bookingForm";
    }

    @PostMapping("/book")
    public String bookSeats(@RequestParam("screen") Long screenId,
                            @RequestParam("seats") int numberOfSeats,
                            Principal principal) {
        User user = null;
        if (principal != null) {
            user = bookingService.getUserByUsername(principal.getName());
        }

        bookingService.bookSeats(screenId, numberOfSeats, user);

        return "redirect:/";
    }
}
