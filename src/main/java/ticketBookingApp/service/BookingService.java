package ticketBookingApp.service;

import ticketBookingApp.entity.User;

public interface BookingService{
    User getUserByUsername(String username);
    void bookSeats(Long screenId, int numberOfSeats, User user);
}
