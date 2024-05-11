package ticketBookingApp.service;

import ticketBookingApp.entity.User;

public interface UserService {
    boolean authenticate(String username, String password);

    void signup(User user);
}
